import sys
from Modules import *

def process(platform):
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

        if "release" not in notes:
            continue

        version = notes["release"]
        master_note = get_master_note(platform, version)

        if "feature" in master_note:
            master_note["feature"].extend(notes["feature"])
        else:
            master_note["feature"] = notes["feature"]

        if "fix" in master_note:
            master_note["fix"].extend(notes["fix"])
        else:
            master_note["fix"] = notes["fix"]

        if "internal" in master_note:
            master_note["internal"].extend(notes["internal"])
        else:
            master_note["internal"] = notes["internal"]

        # Remove the individual releaes notes file
        remove(file_path)

        # Save the master note into the releases folder
        write_release_notes(platform, master_note, version)

### --- MAIN --- ###

clear_terminal()

if is_working_copy_clean() is False:
    print("\nWorking copy is not clean\n")
    sys.exit()

branch = current_branch_name()

if branch != "develop":
    print("\n\nThis script must only be run on develop")
    sys.exit()

process("iOS")
process("tvOS")
