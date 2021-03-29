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

def commit_release_notes(version):
    run("git add .")
    run("git commmit -am \"[ci skip] Creating release for version: %s\"" % (version))
    run("git push")

def create_release_branch(version):
    run("git checkout -b %s" % (version))
    run("git commit -am \"Creating release branch for version: %s\"" % (version))
    run("git push")

### --- MAIN --- ###

clear_terminal()

if is_working_copy_clean() is False:
    print("\nWorking copy is not clean\n")
    sys.exit()

branch = current_branch_name()

if branch == "develop":
    platform = get_platform()
    project_version = project_version_number(platform)
    collate_release_notes(platform, project_version)
    commit_release_notes(project_version)

    if platform == "iOS":
        # Create iOS release
        print("Create iOS release")
        create_release_branch(project_version)
    else:
        # Create tvOS release
        print("Create tvOS release")

elif "release/" in branch:
    # Create iOS Patch Relase Branch
    print("Create iOS Patch Relase Branch")
    project_version = project_version_number("iOS")

elif "release_tvos/" in branch:
    # Create tvOS Patch Release Branch
    print("Create tvOS Patch Release Branch")
    project_version = project_version_number("tvOS")

else:
    print("\n\nYour current branch is is not valid to create a release from.")
    print("\nPlease checkout develop to create a main release, or checkout an existing release branch to create a new patch release branch.\n\n")
