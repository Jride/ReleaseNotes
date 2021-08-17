import sys
import os
from Modules import *

# import logging
# logging.basicConfig(level=logging.DEBUG)

from slack import WebClient
from slack.errors import SlackApiError

client = WebClient(token=os.path.expandvars('$SLACK_BOT_USER_TOKEN'))

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

    for version in updated_release_notes.keys():
        if version in slack_message_ids:
            update_slack_message(message_ids[version])
        else:
            message_id = send_slack_message(platform, updated_release_notes[version])
            slack_message_ids[version] = message_id

    if len(updated_release_notes.keys()) > 0:
        update_slack_message_ids(slack_message_ids, platform)
        return True
    else:
        return False
    

def send_slack_message(platform, master_note):
    release_version = master_note["release"]
    try:
        response = client.chat_postMessage(
            channel=get_slack_channel(platform),
            text="Added new release notes for version %s" % (release_version)
        )

        # return the message id
        return response["ts"]

    except SlackApiError as e:
      print(e.response["error"])
      sys.exit()

def update_slack_message(platform, master_note, message_id):

    try:
        client.chat_update(
          channel=get_slack_channel(platform),
          ts=message_id,
          text="updates from your app again! :tada:"
        )

    except SlackApiError as e:
      print(e.response["error"])

### --- MAIN --- ###

clear_terminal()

if is_working_copy_clean() is False:
    print("\nWorking copy is not clean\n")
    sys.exit()

branch = current_branch_name()

if branch != "develop":
    print("\n\nThis script must only be run on develop")
    sys.exit()

did_process_ios = process("iOS")
did_process_tvos = process("tvOS")

if did_process_ios is False and did_process_tvos is False:
    print("No release notes were updated")
    sys.exit()

run("git add .")
run("git commit -am \"[ci skip] Updating release notes.")
run("git push")
