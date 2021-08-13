import subprocess
import os
import sys
import glob
import yaml

### Executes a shell command and prints the output
def run(command):
    subprocess.run(command, shell=True)

### Executes a shell command silently and returns the output
def result(command, suppress_err=False):
    if suppress_err:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    return result.stdout.decode('utf-8').rstrip()

def clear_terminal():
    run("clear && printf '\e[3J'")

### The name of the current git branch
def current_branch_name():
    branch = result('git rev-parse --abbrev-ref HEAD --', suppress_err=True)
    return branch.splitlines()[0].strip()

def github_homepage():
    string = result("git remote get-url origin", suppress_err=True)
    string = string.replace(".git", "")
    return string

### Returns whether the working copy is clean
def is_working_copy_clean():
    return 'working tree clean' in result('git status')

def get_modified_files():
    modified = []
    for line in result('git status').splitlines():
        if "modified:" in line:
            modified.append(line)

    return modified


### Prompts the user to answer a y/n question (returns bool)
def yes_or_no_input(question):
    result = ""
    while result != "y" and result != "n":
        print(question + " [y/n]")
        result = input()
    return (result == "y")

### Checks if a file exists at a path
def does_file_exist(path):
    return os.path.isfile(path)

def remove(path):
    if os.path.isfile(path):
        os.remove(path)

def choose_from_list(question, options):
    chosen_index = None
    while chosen_index is None:
        print(question)
        for index, option in enumerate(options):
            print("%s. %s" % (index + 1, option))
        print("")
        user_input = input()
        if user_input.isdigit() is True:
            choice = int(user_input) - 1
            if choice is not None and choice >= 0 and choice < len(options):
                chosen_index = choice
        if chosen_index is None:
            print("")

    return choice

def write_release_notes(platform, notes, version):
    file = open(get_release_notes_path(platform, version), "w+")
    yaml.dump(notes, file)
    file.close()

def get_release_notes_path(platform, version):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "ReleaseNotes")
    file_path = os.path.join(file_path, platform)
    file_path = os.path.join(file_path, "Releases")
    file_name = version + ".yml"
    file_path = os.path.join(file_path, file_name)
    return file_path

def get_master_note(platform, version):
    file_path = get_release_notes_path(platform, version)

    master_note = {
        "platform": platform,
        "release": version,
        "feature": [],
        "fix": [],
        "internal": []
    }

    if does_file_exist(file_path) is False:
        return master_note

    file = open(file_path)
    try:
        master_note = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print("Error reading yaml file")
        print(exc)

    return master_note

def get_root_plist_version():
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "iOS")
    file_path = os.path.join(file_path, "Settings")
    file_path = os.path.join(file_path, "Settings.bundle")
    file_path = os.path.join(file_path, "Root.plist")

    with open(file_path, 'r') as file:
        file_lines = file.readlines()

    for index, line in enumerate(file_lines): 
        if "DefaultValue" in line:
            version = file_lines[index + 1]
            version = version.replace("<string>", "")
            version = version.replace("</string>", "")
            return version.strip()

    return None

def release_branch_name(platform, version):
    prefix = "release"
    if platform == "tvOS":
        prefix = "release_tvos"

    branch_name = "%s/%s" % (prefix, version)

    return branch_name

def does_release_branch_exist(platform, version):
    branch_name = release_branch_name(platform, version)
    git_result = result("git ls-remote --exit-code . origin/%s" % (branch_name))
    if branch_name in git_result:
        return True
    else:
        return False

def project_version_number(platform):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, platform)
    file_path = os.path.join(file_path, "ITVHub_" + platform + ".xcodeproj")
    file_path = os.path.join(file_path, "project.pbxproj")

    with open(file_path, 'r') as file:
        project_file_lines = file.readlines()

    for line in project_file_lines:
        line = line.strip()
        if "MARKETING_VERSION" in line:
            version = line.replace(" ", "").replace(";", "").split("=")
            return version[-1].strip()

    print("Was unable to retrieve the version number from the project file...")
    sys.exit()

def collate_release_notes(platform, version):
    working_dir = os.getcwd()
    file_path = os.path.join(working_dir, "ReleaseNotes")
    file_path = os.path.join(file_path, platform)
    file_path = os.path.join(file_path, "Notes")
    file_path = os.path.join(file_path, "*.yml")

    file_paths = glob.glob(file_path)

    master_note = get_master_note(platform, version)

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

        if "feature" in notes:
            master_note["feature"].extend(notes["feature"])
        if "fix" in notes:
            master_note["fix"].extend(notes["fix"])
        if "internal" in notes:
            master_note["internal"].extend(notes["internal"])

        # Remove the individual releaes notes file
        remove(file_path)

    # Save the master note into the releases folder
    write_release_notes(platform, master_note, version)

    return True

def commit_release_notes(version):
    run("git add .")
    run("git commit -am \"[ci skip] Adding release notes for version: %s\"" % (version))
    run("git push")
