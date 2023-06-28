import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

def get_platform():
    platforms = [
        "iOS",
        "tvOS"
    ]
    selected_platform = choose_from_list("Select the platform to create the release for?", platforms)
    clear_terminal()
    return platforms[selected_platform]


def create_release_branch(platform, version, should_push=True):
    branch_name = release_branch_name(platform, version)
    run("git pull")
    run("git checkout -b %s" % (branch_name))
    run("git commit -am \"Creating release branch for version: %s\"" % (version))
    run("git push --no-verify --set-upstream origin %s" % (branch_name))

def check_project_files(platform, project_version):
    modified_files = get_modified_files()

    if platform == "iOS":
        required_files = [
            {
                "name": "ITVHub_iOS.xcodeproj",
                "exists": False
            },
            {
                "name": "Settings.bundle/Root.plist",
                "exists": False
            }
        ]
    else:
        required_files = [
            {
                "name": "ITVHub_tvOS.xcodeproj",
                "exists": False
            }
        ]


    if is_working_copy_clean():
        print("Please bump the project version and update the Root.plist, then run script again.")
        sys.exit()

    for file in modified_files:
        for req_file in required_files:
            if req_file["name"] in file:
                req_file["exists"] = True

    for req_file in required_files:
        if req_file["exists"] is False:
            print("Update %s before running script again" % (req_file["name"]))
            sys.exit()

    if platform == "iOS" and project_version != get_root_plist_version():
        print("Project version and Root.plist version do not match!")
        sys.exit()

def collate_release_notes(platform, version):

    create_aws_credentials_if_needed()

    slack_message_ids = get_slack_message_ids(platform)
    file_paths = get_release_notes(platform)
    master_note = get_master_note(platform, version)

    should_continue = False
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

        if "release" in notes:
            print("SKIPPING BECAUSE BELONGS TO EXISTING RELEASE")
            continue

        merge_notes_into_master(notes, master_note)

        # Remove the individual releaes notes file
        remove(file_path)

        should_continue = True

    if should_continue is False:
        return False

    # Save the master note into the releases folder
    write_release_notes(platform, master_note, version)

    message_id = send_slack_message(platform, master_note)
    slack_message_ids[version] = message_id
    update_slack_message_ids(slack_message_ids, platform)

    return True

### --- MAIN --- ###

clear_terminal()

branch = current_branch_name()

if branch == "develop":
    # Create Major Relase Branch

    if is_working_copy_clean() is False:
        print("Working copy is not clean!")
        sys.exit()

    run("git pull")

    platform = get_platform()
    project_version = project_version_number(platform)

    if does_release_branch_exist(platform, project_version) is True:
        print("Cannot create release branch. The %s release branch for version %s already exists" % (platform, project_version))
        sys.exit()

    if collate_release_notes(platform, project_version) is False:
        print("Release has no release notes to process. Something has gone wrong!")
        sys.exit()

    commit_release_notes(project_version)

    create_release_branch(platform, project_version)

    print("\nRelease branch created for %s version %s. \n\nDon't forget to bump Develop!" % (platform, project_version))

elif "release/" in branch or "release_tvos/" in branch:
    # Create iOS / tvOS Patch Relase Branch
    if "release/" in branch:
        platform = "iOS"
    else:
        platform = "tvOS"

    project_version = project_version_number(platform)

    check_project_files(platform, project_version)

    if len(project_version.split(".")) < 3:
        print("Project version does not contain a patch number (ie 11.5.x)")
        sys.exit()

    if does_release_branch_exist(platform, project_version) is True:
        print("Cannot create release branch. The %s release branch for version %s already exists" % (platform, project_version))
        sys.exit()

    if collate_release_notes(platform, project_version) is False:
        print("Patch release has no release notes to process!")

    create_release_branch(platform, project_version)

    print("\nPatch release branch created for %s version %s." % (platform, project_version))

else:
    print("\n\nYour current branch is is not valid to create a release from.")
    print("\nPlease checkout develop to create a new major release, or checkout an existing release branch to create a new patch release branch.\n\n")
