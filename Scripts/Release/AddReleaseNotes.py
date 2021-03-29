import os
import yaml
import sys
from spellchecker import SpellChecker
from pprint import pprint
from Modules import *

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

def get_input_for_category(category):
    clear_terminal()
    print(category.upper() + " - Enter the notes description:\n")
    return input().strip()

def spellcheck(note):
    spell = SpellChecker()
    scripts_dir_path = os.path.dirname(os.path.realpath(__file__))
    ignore_list = os.path.join(scripts_dir_path, "spellcheck-ignore-list.txt")
    spell.word_frequency.load_text_file(ignore_list)
    # Check
    misspelled = spell.unknown(note.split())

    if not misspelled:
        return True

    print("\nFound the following misspelled words:\n")
    pprint(misspelled)

    return yes_or_no_input("\nWould you like to continue anyways?")

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

def add_release_note(platform, category, note_description):

    release_notes = read_release_notes(platform)

    if release_notes is None:
        # Create new release notes dict
        release_notes = {
            category: [note_description]
        }
    else:
        if category in release_notes:
            release_notes[category].append(note_description)
        else:
            release_notes[category] = [note_description]

    write_release_notes(platform, release_notes)
    clear_terminal()

def create_release_note(platform, category=None):
    clear_terminal()

    if category is None:
        category = select_release_note_category()

    note_description = get_input_for_category(category)

    if not note_description or spellcheck(note_description) is False:
        create_release_note(platform, category)
    else:
        if platform == "Both":
            add_release_note("iOS", category, note_description)
            add_release_note("tvOS", category, note_description)
        else:
            add_release_note(platform, category, note_description)

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

if current_branch_name() == "develop":
    print("Please create a feature branch first before adding any release notes")
    sys.exit()

should_continue = True

notes_added_for_platform = []

while should_continue:
    platform = get_platform()
    notes_added_for_platform.append(platform)
    create_release_note(platform)

    should_continue = yes_or_no_input("Would you like to add another release note?")
    clear_terminal()

print("Your release notes have been added to:\n\n")

if "iOS" in notes_added_for_platform or "Both" in notes_added_for_platform:
    print(get_release_notes_path("iOS") + "\n\n")

if "tvOS" in notes_added_for_platform or "Both" in notes_added_for_platform:
    print(get_release_notes_path("tvOS") + "\n\n")
