import subprocess
import os
import sys
import glob
import yaml
import json
import boto3
from datetime import datetime

from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

from botocore.exceptions import ClientError

slack_client = WebClient(token=os.path.expandvars('$SLACK_BOT_USER_TOKEN'))

s3 = boto3.client('s3')
s3_bucket = "itv-hub-test"
s3_content_key = "slack_message_ids"

DEBUG_MODE = False

### Executes a shell command and prints the output
def run(command):
    subprocess.run(command, shell=True)

### Executes a shell command silently and returns the output
def result(command, suppress_err=False):
    if suppress_err:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    return result.stdout.decode('utf-8').rstrip()

def clear_terminal():
    subprocess.call('clear; printf "\033c"', shell=True)

### The name of the current git branch
def current_branch_name():
    branch = result('git rev-parse --abbrev-ref HEAD --', suppress_err=True)
    return branch.splitlines()[0].strip()

def github_homepage():
    string = result("git remote get-url origin", suppress_err=True)
    string = string.replace(".git", "")
    return string

### Returns whether the working copy is clean
def is_working_copy_clean():
    return 'working tree clean' in result('git status')

def get_modified_files():
    modified = []
    for line in result('git status').splitlines():
        if "modified:" in line:
            modified.append(line)

    return modified


### Prompts the user to answer a y/n question (returns bool)
def yes_or_no_input(question):
    result = ""
    while result != "y" and result != "n":
        print(question + " [y/n]")
        result = input()
    return (result == "y")

def create_file(path):
    open(path, 'a').close()

### Checks if a file exists at a path
def does_file_exist(path):
    return os.path.isfile(path)

def remove(path):
    if os.path.isfile(path):
        os.remove(path)

def choose_from_list(question, options):
    chosen_index = None
    while chosen_index is None:
        print(question)
        for index, option in enumerate(options):
            print("%s. %s" % (index + 1, option))
        print("")
        user_input = input()
        if user_input.isdigit() is True:
            choice = int(user_input) - 1
            if choice is not None and choice >= 0 and choice < len(options):
                chosen_index = choice
        if chosen_index is None:
            print("")

    return choice

def write_release_notes(platform, notes, version):
    file = open(get_release_notes_path(platform, version), "w+")
    yaml.dump(notes, file)
    file.close()

def get_release_notes_path(platform, version):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "ReleaseNotes")
    file_path = os.path.join(file_path, platform)
    file_path = os.path.join(file_path, "Releases")
    file_name = version + ".yml"
    file_path = os.path.join(file_path, file_name)
    return file_path

def get_master_note(platform, version):
    file_path = get_release_notes_path(platform, version)

    if does_file_exist(file_path) is False:
        # If one doesn't exist then return a new master note object
        return {
            "platform": platform,
            "release": version,
            "deployment_target": project_deployment_target(platform)
        }

    file = open(file_path)
    try:
        master_note = yaml.safe_load(file)
        return master_note
    except yaml.YAMLError as exc:
        print("Error reading yaml file")
        print(exc)
        sys.exit()

def get_root_plist_version():
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "iOS")
    file_path = os.path.join(file_path, "Settings")
    file_path = os.path.join(file_path, "Settings.bundle")
    file_path = os.path.join(file_path, "Root.plist")

    with open(file_path, 'r') as file:
        file_lines = file.readlines()

    for index, line in enumerate(file_lines): 
        if "DefaultValue" in line:
            version = file_lines[index + 1]
            version = version.replace("<string>", "")
            version = version.replace("</string>", "")
            return version.strip()

    return None

def release_branch_name(platform, version):
    prefix = "release"
    if platform == "tvOS":
        prefix = "release_tvos"

    branch_name = "%s/%s" % (prefix, version)

    return branch_name

def does_release_branch_exist(platform, version):
    branch_name = release_branch_name(platform, version)
    git_result = result("git ls-remote --exit-code . origin/%s" % (branch_name))
    if branch_name in git_result:
        return True
    else:
        return False

def project_version_number(platform):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, platform)
    file_path = os.path.join(file_path, "ITVHub_" + platform + ".xcodeproj")
    file_path = os.path.join(file_path, "project.pbxproj")

    with open(file_path, 'r') as file:
        project_file_lines = file.readlines()

    for line in project_file_lines:
        line = line.strip()
        if "MARKETING_VERSION" in line:
            version = line.replace(" ", "").replace(";", "").split("=")
            return version[-1].strip()

    print("Was unable to retrieve the version number from the project file...")
    sys.exit()

def project_deployment_target(platform):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, platform)
    file_path = os.path.join(file_path, "ITVHub_" + platform + ".xcodeproj")
    file_path = os.path.join(file_path, "project.pbxproj")

    with open(file_path, 'r') as file:
        project_file_lines = file.readlines()

    if platform == "iOS":
        search_text = "IPHONEOS_DEPLOYMENT_TARGET"
    else:
        search_text = "TVOS_DEPLOYMENT_TARGET"

    for line in project_file_lines:
        line = line.strip()
        if search_text in line:
            deployment_target = line.replace(" ", "").replace(";", "").split("=")
            return deployment_target[-1].strip()

    print("Was unable to retrieve the deployment traget from the project file...")
    sys.exit()

def get_release_notes(platform):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "ReleaseNotes")
    file_path = os.path.join(file_path, platform)
    file_path = os.path.join(file_path, "Notes")
    file_path = os.path.join(file_path, "*.yml")

    return glob.glob(file_path)

def merge_notes_into_master(notes, master_note):
    if "feature" in notes:
        if "feature" in master_note:
            master_note["feature"].extend(notes["feature"])
        else:
            master_note["feature"] = notes["feature"]

    if "fix" in notes:
        if "fix" in master_note:
            master_note["fix"].extend(notes["fix"])
        else:
            master_note["fix"] = notes["fix"]

    if "internal" in notes:
        if "internal" in master_note:
            master_note["internal"].extend(notes["internal"])
        else:
            master_note["internal"] = notes["internal"]

def create_aws_credentials_if_needed():
    aws_creds_path = os.path.expanduser("~/.aws/credentials")

    # Creates the directory if needed
    if not os.path.exists(os.path.dirname(aws_creds_path)):
        try:
            os.makedirs(os.path.dirname(aws_creds_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    if does_file_exist(aws_creds_path) is False:
        access_key_id = os.path.expandvars('$AWS_ACCESS_KEY_ID')
        secret_access_key = os.path.expandvars('$AWS_SECRET_ACCESS_KEY')
        file = open(aws_creds_path, "w+")
        file.writelines('''
[default]
aws_access_key_id = %s
aws_secret_access_key = %s
        ''' % (access_key_id, secret_access_key))
        file.close()

# Slack Related helpers

def slack_message_divider():
    return { "type": "divider" }

def slack_message_header(text):
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": True
        }
    }

def slack_message_sections(text_blocks):
    section_blocks = []

    for text in text_blocks:
        section_blocks.append({
        "type": "section",
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": True
        }
        }) 

    return section_blocks

def slack_message_metadata(master_note):
    now = datetime.now()
    date_time = now.strftime("%d %B, %Y @%I:%M %p")
    platform = master_note["platform"]
    supports = "%s %s and above" % (platform, master_note["deployment_target"])
    return {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Platform:*\n%s" % (master_note["platform"])
            },
            {
                "type": "mrkdwn",
                "text": "*Created:*\n%s" % (date_time)
            },
            {
                "type": "mrkdwn",
                "text": "*Supports:*\n%s" % (supports)
            }
        ]
    }

def slack_text_from_notes_list(notes):

    text_blocks = []

    text = ""
    for note in notes:
        text += "• %s" % note
        # Break up the text blocks as Slack has a character limit
        if len(text) > 1000:
            text_blocks.append(text)
            text = ""
        else:            
            text += "\n"

    if len(text) > 0:
        text_blocks.append(text)
    
    return text_blocks

def slack_message_blocks(master_note):
    blocks = [
        slack_message_header("Version %s" % master_note["release"]),
        slack_message_metadata(master_note)
    ]

    if "feature" in master_note:
        text_blocks = slack_text_from_notes_list(master_note["feature"])
        blocks.extend([
            slack_message_header("Features"),
            slack_message_divider()
        ])
        blocks.extend(slack_message_sections(text_blocks))

    if "fix" in master_note:
        text_blocks = slack_text_from_notes_list(master_note["fix"])
        blocks.extend([
            slack_message_header("Fixes"),
            slack_message_divider()
        ])
        blocks.extend(slack_message_sections(text_blocks))

    if "internal" in master_note:
        text_blocks = slack_text_from_notes_list(master_note["internal"])
        blocks.extend([
            slack_message_header("Internal"),
            slack_message_divider()
        ])
        blocks.extend(slack_message_sections(text_blocks)) 

    return blocks

def send_slack_message(platform, master_note):

    try:
        response = slack_client.chat_postMessage(
            channel=get_slack_channel(platform),
            blocks=slack_message_blocks(master_note)
        )

        # return the message id
        return response["ts"]

    except SlackApiError as e:
      print(e.response["error"])
      sys.exit()

def update_slack_message(platform, master_note, message_id):

    try:
        slack_client.chat_update(
          channel=get_slack_channel(platform),
          ts=message_id,
          blocks=slack_message_blocks(master_note)
        )

    except SlackApiError as e:
      print(e.response["error"])

def get_slack_message_ids(platform):

    key = "%s_%s.json" % (s3_content_key, platform)

    try:
        response = s3.get_object(
            Bucket=s3_bucket,
            Key=key
        )

        file_content = response['Body'].read().decode('utf-8')

        json_object = json.loads(file_content)
        
        return json_object

    except ClientError as ex:

        if ex.response['Error']['Code'] == 'NoSuchKey':
            print('No object found - returning empty')
            return dict()
        else:
            print("Failed to fetch slack message ids from s3 bucket")
            print(ex.response)
            sys.exit()
        

def update_slack_message_ids(json_object, platform):

    key = "%s_%s.json" % (s3_content_key, platform)

    s3.put_object(
         Body=json.dumps(json_object),
         Bucket=s3_bucket,
         Key=key
    )

def get_slack_channel(platform):
    if platform == "iOS":
        # itv-hub-ios-releases
        # return "C02B8F6R84S"
        # slack-integration-test
        return "C05C6EX4ATB"
    else:
        # itv-hub-tvos-releases
        # return "C02BLCY13K6"
        # slack-integration-test
        return "C05C6EX4ATB"

def delete_slack_message(channel_id, message_id):
    try:
        slack_client.chat_delete(
            channel=channel_id,
            ts=message_id
        )

    except SlackApiError as e:
        print("Slack API Error: %s" % e)

def delete_all_slack_messages(platform):
    channel_id = get_slack_channel(platform)
    conversation_history = []
    try:
        # conversations.history returns the first 100 messages by default
        # These results are paginated, see: https://api.slack.com/methods/conversations.history$pagination
        result = slack_client.conversations_history(channel=channel_id)

        conversation_history = result["messages"]

        for message in conversation_history:
            delete_slack_message(channel_id, message["ts"])

    except SlackApiError as e:
        print("Slack API Error: %s" % e)

def show_prompt(arguments):

    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "Scripts")
    file_path = os.path.join(file_path, "AppKit")
    file_path = os.path.join(file_path, "bin")
    file_path = os.path.join(file_path, "AppKitPrompt")
    prompt = file_path

    json_string = json.dumps(arguments)

    command = "'%s' '%s'" % (prompt, json_string)

    input_result = result(command, suppress_err = DEBUG_MODE == False)

    response = json.loads(input_result)

    if "error" in response:
        print(response["error"])
        exit(1)

    if "logs" in response:
        if DEBUG_MODE:
            print(response["logs"])

    return response

def select_folder_path():
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "Scripts")
    file_path = os.path.join(file_path, "AppKit")
    file_path = os.path.join(file_path, "bin")
    file_path = os.path.join(file_path, "FinderSelection")
    finder_prompt = file_path

    command = "'%s'" % (finder_prompt)

    input_result = result(command, suppress_err = DEBUG_MODE == False)

    response = json.loads(input_result)

    if "error" in response:
        print(response["error"])
        exit(1)

    if "logs" in response:
        if DEBUG_MODE:
            print(response["logs"])

    selected_folder_path = response["selected_folder_path"]
    did_cancel_selection = response["did_cancel_selection"]

    if did_cancel_selection == "true":
        print("Push aborted...")
        exit(1)

    return selected_folder_path

def send_pull_request_slack_message(blocks):
    try:
        response = slack_client.chat_postMessage(
            # ios-developmet == C056PB12F
            channel="C05C6EX4ATB",
            blocks=blocks
        )

        # return the message id
        return response["ts"]

    except SlackApiError as e:
      print(e.response["error"])
      sys.exit()
