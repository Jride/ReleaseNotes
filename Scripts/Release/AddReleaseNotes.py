import os
import yaml
import sys
import json
from pprint import pprint

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from Shared.Utils import *

######################
##### Text Input #####
######################
def appkit_text_input(title=None):

    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "Scripts")
    file_path = os.path.join(file_path, "Release")
    file_path = os.path.join(file_path, "TextInput")
    textInput = file_path

    command = "\"%s\"" % (textInput)
    if title is not None:
        command += " \"%s\"" % title

    input_result = result(command)
    response = json.loads(input_result)

    if "error" in response:
        print(response["error"])
        exit(0)

    return response["text"]

def write_release_notes(platform, notes):
    file = open(get_release_notes_path(platform), "w+")
    yaml.dump(notes, file)
    file.close()

def read_release_notes(platform):
    file_path = get_release_notes_path(platform)
    if does_file_exist(file_path) is False:
        return None

    file = open(file_path)
    notes = None

    try:
        notes = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print("Error reading yaml file")
        print(exc)

    file.close()
    return notes

def select_release_note_category():
    categories = [
        "Feature",
        "Fix",
        "Internal"
    ]
    selected_category = choose_from_list("Select Release Note Category", categories)
    return categories[selected_category].lower()

def get_input(category, platform):
    clear_terminal()
    
    if platform == "Both":
        platform = "iOS & tvOS"

    title = "Release Note for %s\nCategory: %s" % (platform, category.capitalize())
    text_input = appkit_text_input(title)
    return text_input.strip()

def get_release_notes_path(platform):
    branch_name = current_branch_name()
    branch_name = branch_name.split("/")[-1]
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "ReleaseNotes")
    file_path = os.path.join(file_path, platform)
    file_path = os.path.join(file_path, "Notes")
    file_name = branch_name + ".yml"
    file_path = os.path.join(file_path, file_name)
    return file_path

def add_full_stop_to_note_if_necessary(note):
    last_character = note[len(note) - 1]
    
    if (last_character != "."):
        return note + "."
    else:
        return note

def add_release_note(platform, category, note_description, release_version=None):

    release_notes = read_release_notes(platform)
    sanitised_note = add_full_stop_to_note_if_necessary(note_description)
    
    if release_notes is None:
        # Create new release notes dict
        release_notes = {
            category: [sanitised_note]
        }
    else:
        if category in release_notes:
            release_notes[category].append(sanitised_note)
        else:
            release_notes[category] = [sanitised_note]

    if release_version is not None:
        release_notes["release"] = release_version

    write_release_notes(platform, release_notes)
    clear_terminal()

def create_release_note(platform, category=None, include_version=False, note_description=None):
    clear_terminal()

    if category is None:
        category = select_release_note_category()

    while note_description is None or not note_description:
        note_description = get_input(category, platform)

    if platform == "Both":
        create_release_note("iOS", category, include_version, note_description)
        create_release_note("tvOS", category, include_version, note_description)
    else:
        release_version = None
        if include_version is True:
            release_version = project_version_number(platform)
        add_release_note(platform, category, note_description, release_version)

def get_platform():
    platforms = [
        "iOS",
        "tvOS",
        "Both"
    ]
    selected_platform = choose_from_list("What platform do the changes affect?", platforms)
    return platforms[selected_platform]

### --- MAIN --- ###

clear_terminal()

branch = current_branch_name()

if branch == "develop" or "/wip" in branch or "release/" in branch:
    print("\nUnsupported branch to create release note in.\n\nPlease use 'gitfeature' to create a feature branch first before continuing.\n")
    sys.exit()

should_continue = True

notes_added_for_platform = []

while should_continue:
    platform = get_platform()

    include_version = False
    if "release_" in branch:
        include_version = True

    notes_added_for_platform.append(platform)

    create_release_note(platform, category=None, include_version=include_version)
    should_continue = yes_or_no_input("Would you like to add another release note?")
    clear_terminal()

print("Your release notes have been added to:\n\n")

if "iOS" in notes_added_for_platform or "Both" in notes_added_for_platform:
    print(get_release_notes_path("iOS") + "\n\n")

if "tvOS" in notes_added_for_platform or "Both" in notes_added_for_platform:
    print(get_release_notes_path("tvOS") + "\n\n")
