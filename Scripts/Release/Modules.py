import subprocess
import os
import sys
import glob
import yaml
import json
import boto3
from datetime import datetime

from slack import WebClient
from slack.errors import SlackApiError
from botocore.exceptions import ClientError

slack_client = WebClient(token=os.path.expandvars('$SLACK_BOT_USER_TOKEN'))

s3 = boto3.client('s3')
s3_bucket = "itv-hub-release-notes"
s3_content_key = "slack_message_ids"

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
    run("clear && printf '\e[3J'")

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

    master_note = {
        "platform": platform,
        "release": version,
        "feature": [],
        "fix": [],
        "internal": []
    }

    if does_file_exist(file_path) is False:
        return master_note

    file = open(file_path)
    try:
        master_note = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print("Error reading yaml file")
        print(exc)

    return master_note

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

def get_release_notes(platform):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "ReleaseNotes")
    file_path = os.path.join(file_path, platform)
    file_path = os.path.join(file_path, "Notes")
    file_path = os.path.join(file_path, "*.yml")

    return glob.glob(file_path)

def collate_release_notes(platform, version):

    slack_message_ids = get_slack_message_ids(platform)
    file_paths = get_release_notes(platform)
    master_note = get_master_note(platform, version)

    should_continue = False
    for file_path in file_paths:
        notes = None
        file = open(file_path)

        try:
            notes = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print("Error reading yaml file")
            print(exc)

        file.close()

        if notes is None:
            continue

        if "release" in notes:
            print("SKIPPING BECAUSE BELONGS TO EXISTING RELEASE")
            continue

        merge_notes_into_master(notes, master_note)

        # Remove the individual releaes notes file
        remove(file_path)

        should_continue = True

    if should_continue is False:
        return False

    # Save the master note into the releases folder
    write_release_notes(platform, master_note, version)

    message_id = send_slack_message(platform, master_note)
    slack_message_ids[version] = message_id
    update_slack_message_ids(slack_message_ids, platform)

    return True

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

def commit_release_notes(version):
    run("git add .")
    run("git commit -am \"[ci skip] Adding release notes for version: %s\"" % (version))
    run("git push")

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

def slack_message_section(text):
    return {
        "type": "section",
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": True
        }
    }

def slack_message_metadata(master_note):
    now = datetime.now()
    date_time = now.strftime("%d %B, %Y @%I:%M %p")
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
            }
        ]
    }

def slack_text_from_notes_list(notes):
    text = "\n• ".join(notes)
    return "• %s" % text

def slack_message_blocks(master_note):
    blocks = [
        slack_message_header("Version %s" % master_note["release"]),
        slack_message_metadata(master_note)
    ]

    if "feature" in master_note:
        text = slack_text_from_notes_list(master_note["feature"])
        blocks.extend([
            slack_message_header("Features"),
            slack_message_divider(),
            slack_message_section(text)
        ])

    if "fix" in master_note:
        text = slack_text_from_notes_list(master_note["fix"])
        blocks.extend([
            slack_message_header("Fixes"),
            slack_message_divider(),
            slack_message_section(text)
        ])

    if "internal" in master_note:
        text = slack_text_from_notes_list(master_note["internal"])
        blocks.extend([
            slack_message_header("Internal"),
            slack_message_divider(),
            slack_message_section(text)
        ]) 

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
        return "C02B8F6R84S"
    else:
        # itv-hub-tvos-releases
        return "C02BLCY13K6"

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
