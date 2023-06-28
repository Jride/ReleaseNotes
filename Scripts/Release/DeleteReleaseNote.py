import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

def get_platform():
    platforms = [
        "iOS",
        "tvOS"
    ]
    selected_platform = choose_from_list("What platform release note to delete?", platforms)
    return platforms[selected_platform]

### --- MAIN --- ###

platform = get_platform()
channel_id = get_slack_channel(platform)

print("Enter the slack message id you wish to delete:\n")
message_id = input().strip()

delete_slack_message(channel_id, message_id)