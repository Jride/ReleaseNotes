import sys
import os
import base64
import re
import requests
from git import Repo

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

class FeatureFlag:
    key = None
    name = None
    note = None

    def is_complete(self):
        if self.key is not None and self.name is not None and self.note is not None:
            return True
        else:
            return False

    def json_str(self):
        return '{"key":"%s","name":"%s","note":"%s"}' % (self.key, self.name, self.note)

def get_platform():
    print("\n")
    platforms = [
        "iOS",
        "tvOS"
    ]
    selected_platform = choose_from_list("What platform is the TestFlight build for?", platforms)
    return platforms[selected_platform]

def get_is_stakeholder_build():
    print("\n")
    options = [
        "yes",
        "no"
    ]
    selected_option = choose_from_list("Is this TF build for stakeholders? If yes then a slack notification will be posted into the itv-regression channel.", options)
    return options[selected_option]

def get_input(question):
    print("")
    print(question)
    return input()

def update_flag_property(flag, line):

    # Get contents between double quotes
    results = re.findall('"([^"]*)"', line)

    if "key:" in line:
        value = results[0]
        flag.key = value

    if "name:" in line:
        value = results[0]
        flag.name = value

    if "note:" in line:
        value = results[0]
        flag.note = value

    return flag
    
def get_flag_definitions_path():
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "Frameworks")
    file_path = os.path.join(file_path, "Core")
    file_path = os.path.join(file_path, "Core")
    file_path = os.path.join(file_path, "Services")
    file_path = os.path.join(file_path, "Feature Flagging")
    file_path = os.path.join(file_path, "Feature Flag Definitions")
    return file_path

def get_feature_flag_options(platform):

    shared_flags_path = os.path.join(get_flag_definitions_path(), "FeatureFlags+Shared.swift")
    shared_flags_file = open(shared_flags_path, "r")
    shared_flags = shared_flags_file.readlines()
    shared_flags_file.close()

    if platform == "ios":
        platform_flags_path = os.path.join(get_flag_definitions_path(), "FeatureFlags+iOS.swift")
    else:
        platform_flags_path = os.path.join(get_flag_definitions_path(), "FeatureFlags+tvOS.swift")

    platform_flags_file = open(platform_flags_path, "r")
    platform_flags = platform_flags_file.readlines()
    platform_flags_file.close()

    all_flags_lines = shared_flags + platform_flags

    current_flag = FeatureFlag()
    all_feature_flags = []
    for line in all_flags_lines:
        current_flag = update_flag_property(current_flag, line)

        if current_flag.is_complete():
            all_feature_flags.append(current_flag)
            current_flag = FeatureFlag()

    return all_feature_flags

def name(flag):
    return flag.name

def select_flags(all_flags, selected_flags = []):

    selected_flag_names = list(map(name, selected_flags))

    filtered_flags = []
    for flag in all_flags:
        if flag.name in selected_flag_names:
            continue

        filtered_flags.append(flag)

    choices = list(map(name, filtered_flags))
    choices.insert(0, "Continue...")
    selected_index = choose_from_list("Select the feature flag you wish to have enabled or select 'Continue' to proceed:", choices)
    
    if selected_index == 0:
        return selected_flags
    
    selected_index = selected_index - 1
    selected_flags.append(filtered_flags[selected_index])

    clear_terminal()

    return select_flags(all_flags, selected_flags)

def add_bitrise_access_token_to_keychain():
    token = input("Please enter the Bitrise access token now: ")
    
    print("\n\nAdding access token to keychain...")
    command = "security add-generic-password -a bitrise_testflight -s bitrise_testflight_token -w '%s'" % token
    subprocess.run(command, shell = True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return token

def get_bitrise_access_token_from_keychain():
    command = "security find-generic-password -a bitrise_testflight -s bitrise_testflight_token -w"
    token = subprocess.run(command, shell = True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode('utf-8').rstrip()

    if not token:
        print("\n ❌ There was no bitrise_testflight access token set in the keychain. ❌\n")
        print("You can find the 🔑 Bitrise Access Token 🔑 in 1Password in the iOS vault\n")
        return add_bitrise_access_token_to_keychain()

    return token

def fetch_recent_release_branches(platform):
    # Returns the 5 most recent release branches for the selected platform
    repo = Repo('.')
    origin = repo.remotes.origin
    origin.fetch()

    branch_name = "release/" if platform == "ios" else "release_tvos/"
    
    branches = [branch.remote_head for branch in origin.refs if branch.remote_head.startswith(branch_name)]
    recent_branches = sorted(branches, key=lambda x: origin.refs[x].commit.committed_datetime, reverse=True)[:5]
    return recent_branches

def get_branch(platform, is_stakeholder_build):

    if is_stakeholder_build == "yes":
        recent_release_branches = fetch_recent_release_branches(platform)
        selected_branch = choose_from_list("What release is the TestFlight build for?", recent_release_branches)
        return recent_release_branches[selected_branch]
    else:
        return get_input("Enter the name of the branch you wish to create the TestFlight build for:")

### --- MAIN --- ###

token = get_bitrise_access_token_from_keychain()

platform = get_platform().lower()

is_stakeholder_build = get_is_stakeholder_build()

branch = get_branch(platform, is_stakeholder_build)

flags = get_feature_flag_options(platform)
selected_flags = select_flags(flags)

flags_json = []
for flag in selected_flags:
    flags_json.append(flag.json_str())

flags_json_str = ','.join(flags_json)
json_str = '{"flags":[%s]}' % flags_json_str
flags_json_str_base64 = base64.b64encode(json_str.encode()).decode('utf-8')

what_to_test = get_input("Include a description of what the user should test:")
what_to_test_base64 = base64.b64encode(what_to_test.encode()).decode('utf-8')

clear_terminal()

url = "https://api.bitrise.io/v0.1/apps/cbe8701b82f451e1/builds"
headers = {
    "accept": "application/json",
    "Authorization": token,
    "Content-Type": "application/json"
}
data = {
    "hook_info": {
        "type": "bitrise"
    },
    "build_params": {
        "branch": branch,
        "commit_message": "TestFlight Upload",
        "workflow_id": "TestFlight_Upload",
        "environments": [
            {
                "mapped_to": "ENABLED_FEATURE_FLAGS",
                "value": flags_json_str_base64,
                "is_expand": True
            },
            {
                "mapped_to": "PLATFORM",
                "value": platform,
                "is_expand": True
            },
            {
                "mapped_to": "WHAT_TO_TEST",
                "value": what_to_test_base64,
                "is_expand": True
            },
            {
                "mapped_to": "IS_STAKEHOLDER_BUILD",
                "value": is_stakeholder_build,
                "is_expand": True
            }
        ]
    },
    "triggered_by": "curl"
}

try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Raise an exception for any error status code
    json_response = response.json()

    if json_response["status"] == "ok":
        print("\n🎉 TestFlight Build Started Successfully 🎉\n")
        print("🛠️  Build URL  🛠️\n")
        print(json_response["build_url"])
        print("\n")
    else:
        print("Sorry, something went wrong... 🤬\n")
        print(json_response["message"])

except requests.exceptions.RequestException as e:
    # Handle any request exception that occurred
    print(f"Error: {e}")

