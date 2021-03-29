import subprocess
import sys
import os
import glob

############################################################
# Check's to make sure all Feature Flags declared are false
############################################################

### Executes a shell command silently and returns the output
def result(command, suppress_err = False):
    if suppress_err:
        result = subprocess.run(command, shell = True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        result = subprocess.run(command, shell = True, stdout=subprocess.PIPE)

    return result.stdout.decode('utf-8').rstrip()

### MAIN ###

main_dir = os.path.abspath(os.path.join(__file__ ,"../.."))

# Check first to see if FeatureFlags.swift is staged
git_result = result("git diff --name-only --cached")
lines = git_result.splitlines()
is_file_staged = False
for line in lines:
    if "FeatureFlags.swift" in line:
        is_file_staged = True

if is_file_staged == False:
    sys.exit()

feature_flags_file_path = None
for file_name in glob.iglob(main_dir + "/**/FeatureFlags.swift", recursive=True):
    if file_name == __file__:
        continue

    feature_flags_file_path = file_name

if feature_flags_file_path == None:
    print("\n")
    print("Unable to find the FeatureFlags.swift file")
    exit(1)

with open(feature_flags_file_path) as fp:
    found_starting_line = False
    for line in fp:
        line = line.strip()

        if "struct FeatureFlags" in line:
            found_starting_line = True

        if found_starting_line == True and "=" in line:
            line = line.replace(' ', '')
            split_line = line.split("=")
            value = split_line[-1]
            variable = split_line[0]
            variable_name = variable[3:]
            if value == "true":
                print("Feature Flag: '"+ variable_name +"' should be set to false")
                exit(1)