import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

### Main ###

def pre_push_hook():
    working_dir = os.getcwd()
    swiftformat = os.path.join(working_dir, "BuildTools/swiftformat")
    config = os.path.join(working_dir, ".swiftformat")
    folder = os.path.join(working_dir)
    command = '"%s" "%s" --config "%s" --swiftversion 5.8' % (swiftformat, folder, config)

    run(command)

    if is_working_copy_clean() == False:
        # Things have been formatted so commit them here
        run('git commit -am "formatting code with swiftformat" --no-verify')
        return True
    else:
        return False