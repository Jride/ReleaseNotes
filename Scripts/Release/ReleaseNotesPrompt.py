import os
import sys
import glob

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

def __release_notes_dir():
    WORKING_DIR = os.getcwd()
    return os.path.join(WORKING_DIR, "ReleaseNotes")

def __no_notes_dir():
    file_path = __release_notes_dir()
    return os.path.join(file_path, ".no-notes")

def __should_skip_release_notes_check():

    current_branch = current_branch_name().split("/")[-1]
    
    branch_names_to_skip = os.listdir(__no_notes_dir())
    if current_branch in branch_names_to_skip:
        # Skipping release notes check
        return True

    for note in glob.glob(__release_notes_dir() + '/**/*.yml', recursive=True):
        if current_branch in note:
            # Skipping release notes check
            return True

    return False


###################
##### Prompt ######
###################
def __release_notes_prompt():

    response = {
        "should_add_release_notes": False,
        "did_add_new_commit": False
    }
    
    if __should_skip_release_notes_check():
        return response

    arguments = {
        "promptTitle": "Release Notes Prompt",
        "promptText": "No release notes have been added yet. Does this branch require any?",
        "promptLink": "https://github.com/ITV/itvplayer-ios/wiki/Release-Notes#when-to-add-release-notes",
        "promptLinkTitle": "When should you add release notes?",
        "confirmButtonCopy": "No",
        "denyButtonCopy": "Yes, add some now"
    }

    json_response = show_prompt(arguments)

    prompt_response = json_response["promptResponse"]

    current_branch = current_branch_name().split("/")[-1]

    if prompt_response == "true":
        no_notes_file_path = os.path.join(__no_notes_dir(), current_branch)
        create_file(no_notes_file_path)
        run("git add " + no_notes_file_path)
        run("git commit -m \"Marking current branch to have no release notes\"")
        response["did_add_new_commit"] = True
    else:
        response["should_add_release_notes"] = True

    return response


### --- MAIN --- ###

def pre_push_hook():

    result = __release_notes_prompt()

    if result["should_add_release_notes"] == True:

        # Apple Script Command
        cmd = """osascript -e '

            -- Get the users screen size
            tell application "Finder"
                set screenSize to bounds of window of desktop
                set screenWidth to item 3 of screenSize
                set screenHeight to item 4 of screenSize
            end tell

            tell application "Terminal"

                -- Brings the window to the forefront
                activate

                -- Setup terminal window
                set myTab to do script ""
                set myWindow to window 1
                tell myWindow to set selected tab to myTab

                -- Resize terminal window and center of screen
                set the bounds of myWindow to {0, 0, 500, 300}
                set xPos to ((screenWidth / 2) - (500 / 2))
                set yPos to ((screenHeight / 2) - (300 / 2))
                set position of myWindow to {xPos, yPos}
                
                -- Navigate to the repo and execute the add release notes
                do script "cd '%s' && ./add-release-note.sh" in myTab
                
                -- Wait until the add release notes script finishes executing
                repeat
                    delay 1
                    if not busy of myTab then exit repeat
                end repeat

                -- Closes the terminal window and returns
                close myWindow

            end tell

        '
        """ % (os.getcwd())
        
        # Execute
        os.system(cmd)

        if __should_skip_release_notes_check():
            run("git add ReleaseNotes/*")
            run("git commit -m \"Adding release notes\"")
            return True
        else:
            print("Push aborted as no release notes were added. Please try again or run the ./add-release-note.sh script before continuing.")
            exit(1)

    else:
        return result["did_add_new_commit"]