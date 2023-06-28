import os
import sys
import subprocess

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

### Pivate Helper Methods ###

def __ci_xcode_version():
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, ".ci-xcode-version")

    with open(file_path, 'r') as file:
        file_lines = file.readlines()

    return file_lines[0].strip()

def __users_xcode_version():

    output = subprocess.run("xcodebuild -version", shell=True, stdout=subprocess.PIPE)
    for line in output.stdout.decode('utf-8').rstrip().split('\n'):
        line = line.lower()
        if "xcode" in line:
            return line.replace("xcode", "").strip()

    return None


### Main ###

def pre_push_hook():

    local_version = __users_xcode_version()
    ci_version = __ci_xcode_version()

    if local_version != ci_version:

        prompt_text = "Your Xcode version does not match the expected version which our CI is currently using. Ideally everyone should be running on the same version of Xcode so we do not encounter any potential build issues. \n\nLocal Xcode Version: %s\nExpected Xcode Version: %s\n" % (local_version, ci_version)

        arguments = {
            "promptTitle": "⚠️ Xcode Version Mismatch ⚠️",
            "promptText": prompt_text,
            "promptLink": "https://stackoverflow.com/questions/10335747/how-to-download-xcode-dmg-or-xip-file",
            "promptLinkTitle": "Click here for Xcode download links",
            "confirmButtonCopy": "Continue anyways",
            "denyButtonCopy": "Cancel"
        }

        response = show_prompt(arguments)

        prompt_response = response["promptResponse"]

        if prompt_response != "true":
            print("Push aborted...")
            exit(1)

def post_merge_hook():

    local_version = __users_xcode_version()
    ci_version = __ci_xcode_version()

    if local_version != ci_version:

        prompt_text = "Your Xcode version does not match the expected version which our CI is currently using. Ideally everyone should be running on the same version of Xcode so we do not encounter any potential build issues. \n\nLocal Xcode Version: %s\nExpected Xcode Version: %s\n" % (local_version, ci_version)

        arguments = {
            "promptTitle": "⚠️ Xcode Version Mismatch ⚠️",
            "promptText": prompt_text,
            "promptLink": "https://stackoverflow.com/questions/10335747/how-to-download-xcode-dmg-or-xip-file",
            "promptLinkTitle": "Click here for Xcode download links",
            "dismissAlertButtonCopy": "Ok"
        }

        show_prompt(arguments)