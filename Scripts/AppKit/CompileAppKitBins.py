
import os
import glob
import subprocess

working_dir = os.getcwd()
file_path = os.path.join(working_dir, "Scripts")
file_path = os.path.join(file_path, "AppKit")
scripts_dir = file_path

for file_name in glob.iglob(scripts_dir + "/**/_swift_project", recursive=True):

    path_list = file_name.split("/")
    script_name = path_list[-2]
    del path_list[-1]
    path = '/'.join(path_list)
    script_name = scripts_dir + "/bin/" + script_name
    swift_files = glob.glob(path + "/*.swift")

    command = "swiftc -o \"%s\"" % (script_name)

    for file in swift_files:
        command += " \"%s\"" % (file)

    if os.path.exists(script_name):
        os.remove(script_name)

    # Check if there are any compilation errors
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8').rstrip()

    if result is not None and result != "":
        if "error" in result:
            print("\n")
            print("Error Compiling " + script_name)
            print("\n")
            print(result)
            exit(1)
        else:
            print("\n")
            print("Warnings Compiling " + script_name)
            print("\n")
            print(result)

    # Compile swift scripts into single binary and stage it
    
    # command += " && git add \"%s\"" % script_name
    # subprocess.run(command, shell=True)