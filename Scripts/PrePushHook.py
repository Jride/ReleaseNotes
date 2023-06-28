from Release import ReleaseNotesPrompt
from VersionCheck import XcodeVersion, ITVScriptsVersion
from Format import SwiftFormat, CleanWorkingCopy
from Shared import Utils

import subprocess
import os
import sys
import time

if len(sys.argv) == 2:
    time.sleep(7)
    Utils.run("git push --no-verify")

else:
    # Run all pre push hooks
    commit_added = 0

    ITVScriptsVersion.pre_push_hook()

    XcodeVersion.pre_push_hook()

    CleanWorkingCopy.pre_push_hook()

    if SwiftFormat.pre_push_hook():
        commit_added += 1

    if ReleaseNotesPrompt.pre_push_hook():
        commit_added += 1

    if commit_added > 0:
        # Rerun command to push any additional changes made
        subprocess.Popen(['python3', os.path.realpath(__file__), '0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exit(0)
