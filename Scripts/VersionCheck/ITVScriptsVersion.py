import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *
from VersionCheck import ITVScriptsLocationSetup, VersionMismatchPrompt

DEBUG_MODE = False

### Main ###

def pre_push_hook():

    ITVScriptsLocationSetup.setup_if_needed()

    VersionMismatchPrompt.prompt_if_needed()