import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

### Main ###

def setup_if_needed():

    working_dir = os.getcwd()
    itv_scripts_path = os.path.join(working_dir, ".itv-scripts-location")

    if does_file_exist(itv_scripts_path) is False:

        arguments = {
            "promptTitle": "🐍 ITV Python Scripts Setup 🐍",
            "promptText": "You will now be prompted to select the location of where you have installed the iOS teams python scripts. This is required to ensure that the entire team is all on the most up to date version of the scripts.\n\nIf you do not have the scripts installed on your machine yet then follow the link to the repository to get setup.",
            "promptLink": "https://github.com/ITV/iOS-Team-Scripts",
            "promptLinkTitle": "iOS Team Scripts Github Repo",
            "dismissAlertButtonCopy": "Ok"
        }
        
        show_prompt(arguments)

        folder_path = select_folder_path()

        file = open(itv_scripts_path, "w+")
        file.write(folder_path)
        file.close()




        