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
    run("git commit -am \"[ci skip] Creating release for version: %s\"" % (version))
    run("git push")

def release_branch_name(platform, version):
    prefix = "release"
    if platform == "tvOS":
        prefix = "release_tvos"

    branch_name = "%s/%s" % (prefix, version)

    return branch_name

def create_release_branch(platform, version):
    branch_name = release_branch_name(platform, version)
    run("git checkout -b %s" % (branch_name))
    run("git commit -am \"Creating release branch for version: %s\"" % (version))
    run("git push --set-upstream origin %s" % (branch_name))

def does_release_branch_exist(platform, version):
    branch_name = release_branch_name(platform, version)
    git_result = result("git ls-remote --exit-code . origin/%s" % (branch_name))
    if branch_name in git_result:
        return True
    else:
        return False

### --- MAIN --- ###

clear_terminal()

if is_working_copy_clean() is False:
    print("\nWorking copy is not clean\n")
    sys.exit()

branch = current_branch_name()

if branch == "develop":
    platform = get_platform()
    project_version = project_version_number(platform)

    if does_release_branch_exist(platform, project_version) is True:
        print("Cannot create release branch. The %s release branch for version %s already exists" % (platform, project_version))
        sys.exit()

    collate_release_notes(platform, project_version)
    commit_release_notes(project_version)
    create_release_branch(platform, version)

elif "release/" in branch:
    # Create iOS Patch Relase Branch
    project_version = project_version_number("iOS")

elif "release_tvos/" in branch:
    # Create tvOS Patch Release Branch
    project_version = project_version_number("tvOS")

else:
    print("\n\nYour current branch is is not valid to create a release from.")
    print("\nPlease checkout develop to create a new major release, or checkout an existing release branch to create a new patch release branch.\n\n")
