import sys
from Modules import *

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
    run("git checkout -b %s" % (branch_name))
    run("git commit -am \"Creating release branch for version: %s\"" % (version))
    run("git push --set-upstream origin %s" % (branch_name))

def check_project_files(platform):
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

    if platform == "iOS" and project_version_number(platform) != get_root_plist_version():
        print("Project version and Root.plist version do not match!")
        sys.exit()


### --- MAIN --- ###

clear_terminal()

branch = current_branch_name()

if branch == "develop":
    # Create Major Relase Branch

    if is_working_copy_clean() is False:
        print("Working copy is not clean!")
        sys.exit()

    platform = get_platform()
    project_version = project_version_number(platform)

    if does_release_branch_exist(platform, project_version) is True:
        print("Cannot create release branch. The %s release branch for version %s already exists" % (platform, project_version))
        sys.exit()

    if collate_release_notes(platform, project_version) is False:
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

    check_project_files(platform)
    
    if len(project_version.split(".")) < 3:
        print("Project version does not contain a patch number (ie 11.5.x)")
        sys.exit()

    if does_release_branch_exist(platform, project_version) is True:
        print("Cannot create release branch. The %s release branch for version %s already exists" % (platform, project_version))
        sys.exit()

    if collate_release_notes(platform, project_version) is False:
        print("Release has no release notes to process. Something has gone wrong!")
        sys.exit()

    create_release_branch(platform, project_version)

    print("\nPatch release branch created for %s version %s." % (platform, project_version))

else:
    print("\n\nYour current branch is is not valid to create a release from.")
    print("\nPlease checkout develop to create a new major release, or checkout an existing release branch to create a new patch release branch.\n\n")
