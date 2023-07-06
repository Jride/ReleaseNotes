import os
import sys
import webbrowser
import re
import plistlib

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

# Passing in any argument will run this script in CI mode
if len(sys.argv) > 1:
    CI_MODE = True
else:
    CI_MODE = False

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

def github_homepage():
    string = result("git remote get-url origin", suppress_err=True)
    string = string.replace(".git", "")
    return string

def collate_release_notes(platform, version, target_branch):

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

    if target_branch == "develop":
        # Create new branch to merge release notes back into develop
        branch_name = "release-candidate-cut-version-%s" % version
        run("git checkout -b %s" % (branch_name))
        run("git add .")
        run("git commit -am \"Merging release notes for version: %s\"" % (version))
        run("git push --no-verify --set-upstream origin %s" % (branch_name))

    return True

def increment_semantic_version(version, level):
    # Split the version into major, minor, and patch components
    components = version.split('.')

    major = components[0]
    minor = components[1]
    patch = components[2] if len(components) > 2 else ''

    if level == 'major':
        major = str(int(major) + 1)
        minor = '0'
        patch = ''  # Remove patch version
    elif level == 'minor':
        minor = str(int(minor) + 1)
        patch = ''  # Remove patch version
    elif level == 'patch':
        if patch:
            patch = str(int(patch) + 1)
        else:
            patch = '1'

    if len(patch) > 0:
        return f'{major}.{minor}.{patch}'
    else:
        return f'{major}.{minor}'

def bump_marketing_version(platform, level):

    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, platform)
    file_path = os.path.join(file_path, "ITVHub_" + platform + ".xcodeproj")
    pbxproj_path = os.path.join(file_path, "project.pbxproj")

    try:
        # Read the project.pbxproj file
        with open(pbxproj_path, 'r') as pbxproj_file:
            pbxproj_content = pbxproj_file.read()

            # Find and replace the MARKETING_VERSION
            version_regex = r'MARKETING_VERSION = ([0-9.]+);'
            matches = re.findall(version_regex, pbxproj_content)
            if len(matches) > 0:
                current_version = matches[0]
                print('Current MARKETING_VERSION:', current_version)

                # Increment the version based on the specified level
                new_version = increment_semantic_version(current_version, level)

                # Replace the MARKETING_VERSION
                updated_content = re.sub(version_regex, 'MARKETING_VERSION = {};'.format(new_version), pbxproj_content)

                # Write the updated project.pbxproj file
                with open(pbxproj_path, 'w') as updated_file:
                    updated_file.write(updated_content)

                print('MARKETING_VERSION bumped to', new_version, 'successfully.')
            else:
                print('MARKETING_VERSION not found in project.pbxproj.')

    except FileNotFoundError:
        print('project.pbxproj file not found.')
    except Exception as e:
        print('An error occurred:', str(e))

def bump_ios_settings_bundle_plist(level):

    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, platform)
    file_path = os.path.join(file_path, "Settings")
    file_path = os.path.join(file_path, "Settings.bundle")
    plist_path = os.path.join(file_path, "Root.plist")

    try:
        # Load the plist file
        with open(plist_path, 'rb') as plist_file:
            plist_data = plistlib.load(plist_file)

            # Update the DefaultValue key
            if 'PreferenceSpecifiers' in plist_data:
                preference_specifiers = plist_data['PreferenceSpecifiers']
                for specifier in preference_specifiers:
                    if 'DefaultValue' in specifier:
                        specifier['DefaultValue'] = increment_semantic_version(specifier['DefaultValue'], level)

        # Write the updated plist file
        with open(plist_path, 'wb') as plist_file:
            plistlib.dump(plist_data, plist_file)

        print(f'Updated the "DefaultValue" in the plist file: {plist_path}')

    except FileNotFoundError:
        print(f'Plist file not found: {plist_path}')
    except Exception as e:
        print(f'An error occurred while updating the plist file: {str(e)}')

def post_pr_link_to_slack(platform, version, url):

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "A new release candidate has been cut! Click the \"*Open Pull Request*\" button below to get the release notes and incremented version number changes merged into develop 🙏"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Platform:* %s\n*Version:* %s" % (platform, version)
            },
            "accessory": {
                "type": "image",
                "image_url": "https://i.ibb.co/XSX8C1y/git-1.jpg",
                "alt_text": "Pull Request"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Open Pull Request",
                        "emoji": true
                    },
                    "value": "click_me_123",
                    "url": url
                }
            ]
        }
    ]

    send_pull_request_slack_message(blocks)

### --- MAIN --- ###

post_pr_link_to_slack("iOS", "14.16", "http://google.com")
exit(0)

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

    if collate_release_notes(platform, project_version, branch) is False:
        print("Release has no release notes to process. Something has gone wrong!")
        sys.exit()

    create_release_branch(platform, project_version)

    print("\nRelease branch created for %s version %s." % (platform, project_version))

    # Bump version for branch that will be merged back into develop
    branch_name = "release-candidate-cut-version-%s" % project_version
    run("git checkout %s" % (branch_name))

    level = "minor"
    if platform == "iOS":
        bump_ios_settings_bundle_plist(level)

    bump_marketing_version(platform, level)

    run("git add .")
    run("git commit -am \"Bumping marketing version\"")
    run("git push --no-verify --set-upstream origin %s" % (branch_name))

    pr_url = github_homepage() + "/compare/develop..." + branch_name

    if CI_MODE:
        # Post link to open PR
        post_pr_link_to_slack(platform, project_version, pr_url)
    else:
        webbrowser.open(pr_url)

elif "release/" in branch or "release_tvos/" in branch:
    # Create iOS / tvOS Patch Relase Branch

    level = "patch"

    if "release/" in branch:
        platform = "iOS"
        bump_ios_settings_bundle_plist(level)
    else:
        platform = "tvOS"

    bump_marketing_version(platform, level)

    project_version = project_version_number(platform)

    if does_release_branch_exist(platform, project_version) is True:
        print("Cannot create release branch. The %s release branch for version %s already exists" % (platform, project_version))
        sys.exit()

    if collate_release_notes(platform, project_version, branch) is False:
        print("Patch release has no release notes to process, continuing anyways...")

    create_release_branch(platform, project_version)

    print("\nPatch release branch created for %s version %s." % (platform, project_version))

else:
    print("\n\nYour current branch is is not valid to create a release from.")
    print("\nPlease checkout develop to create a new major release, or checkout an existing release branch to create a new patch release branch.\n\n")
