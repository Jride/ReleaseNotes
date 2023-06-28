import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

def checkout_develop():
    run("git checkout develop && git pull")

def process(platform):

    updated_release_notes = {}
    slack_message_ids = get_slack_message_ids(platform)
    file_paths = get_release_notes(platform)

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

        # Only process a note that is tagged for a specific release
        if "release" not in notes:
            continue

        version = notes["release"]
        master_note = get_master_note(platform, version)

        merge_notes_into_master(notes, master_note)

        # Remove the individual releaes notes file
        remove(file_path)

        # Save the master note into the releases folder
        write_release_notes(platform, master_note, version)

        updated_release_notes[version] = master_note

    for key in updated_release_notes.keys():
        if key in slack_message_ids:
            update_slack_message(platform, updated_release_notes[key], slack_message_ids[key])
        else:
            message_id = send_slack_message(platform, updated_release_notes[key])
            slack_message_ids[key] = message_id

    if len(updated_release_notes.keys()) > 0:
        update_slack_message_ids(slack_message_ids, platform)
        return True
    else:
        return False

### --- MAIN --- ###

create_aws_credentials_if_needed()

if is_working_copy_clean() is False:
    print("\nWorking copy is not clean. Cleaning now...\n")
    run("git clean -fd")

branch = current_branch_name()

if branch != "develop":
    print("\n\nThis script must only be run on develop. Checking out develop now...")
    checkout_develop()

did_process_ios = process("iOS")
did_process_tvos = process("tvOS")

if did_process_ios is False and did_process_tvos is False:
    print("No release notes were updated")
    sys.exit()

run("git add .")
run("git commit -am '[ci skip] Updating release notes.'")
run("git push --no-verify")
