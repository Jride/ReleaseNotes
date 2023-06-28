import os
import sys
import subprocess

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

### Pivate Helper Methods ###

def __repo_version():
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, ".itv-scripts-version")
    return open(file_path, 'r').read().strip()

def __local_version():
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, ".itv-scripts-location")
    scripts_path = open(file_path, 'r').read().strip()

    source = 'source "%s/Aliases"' % scripts_path
    command = '%s && python3 "$ITV_PYTHON_SCRIPTS/Help/ITVScripts.py" --version' % source

    output = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    output_string = output.stdout.decode('utf-8').rstrip()

    if "unrecognized arguments" in output_string:
        return "0"

    return output_string


### Main ###

def prompt_if_needed():

    local_version = __local_version()
    repo_version = __repo_version()

    if local_version != repo_version:

        prompt_text = "Your local ITV Scripts version needs updating. \n\nLocal ITV Scripts Version: %s\nExpected ITV Scripts Version: %s\n\nTo get rid of this warning just pull the latest changes from the iOS Team Scripts repo that you have setup on your local machine." % (local_version, repo_version)

        arguments = {
            "promptTitle": "🐍 ITV Python Scripts Version Mismatch 🐍",
            "promptText": prompt_text,
            "promptLink": "https://github.com/ITV/iOS-Team-Scripts",
            "promptLinkTitle": "iOS Team Scripts Github Repo",
            "confirmButtonCopy": "Continue anyways",
            "denyButtonCopy": "Cancel"
        }

        response = show_prompt(arguments)

        prompt_response = response["promptResponse"]

        if prompt_response != "true":
            print("Push aborted...")
            exit(1)