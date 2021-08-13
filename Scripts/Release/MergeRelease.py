import sys
from Modules import *

### --- MAIN --- ###

clear_terminal()

if is_working_copy_clean() is False:
    print("\nWorking copy is not clean\n")
    sys.exit()

branch = current_branch_name()
target_branch = "develop"

pr_url = github_homepage() + "/compare/" + target_branch + "..." + branch

if "release_tvos" in branch:
    platform = "tvOS"
elif "release" in branch:
    platform = "iOS"
else:
    print("\n\nYour current branch is is not valid release branch.")
    sys.exit()

if collate_release_notes(platform, project_version) is True:
    commit_release_notes(project_version)

# -----------

if branch == "develop":
    platform = get_platform()
    project_version = project_version_number(platform)

    if does_release_branch_exist(platform, project_version) is True:
        print("Cannot create release branch. The %s release branch for version %s already exists" % (platform, project_version))
        sys.exit()

    collate_release_notes(platform, project_version)
    commit_release_notes(project_version)
    create_release_branch(platform, project_version)

elif "release/" in branch:
    # Create iOS Patch Relase Branch
    project_version = project_version_number("iOS")

elif "release_tvos/" in branch:
    # Create tvOS Patch Release Branch
    project_version = project_version_number("tvOS")

else:
    print("\n\nYour current branch is is not valid to create a release from.")
    print("\nPlease checkout develop to create a new major release, or checkout an existing release branch to create a new patch release branch.\n\n")
