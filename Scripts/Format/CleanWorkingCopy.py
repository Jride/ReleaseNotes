import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

def pre_push_hook():

    if is_working_copy_clean():
        print("Working copy is clean..")
        return

    arguments = {
        "promptTitle": "🧹 Clean Git Working Copy 🧹",
        "promptText": "Your working copy is not clean. The pre-push commit hook requires you to commit or stash any remaining changes prior to pushing anything to the repo.",
        "dismissAlertButtonCopy": "Ok"
    }
    
    response = show_prompt(arguments)

    prompt_response = response["promptResponse"]

    if prompt_response != "true":
        print("Push aborted...")
        exit(1)
