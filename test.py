import re
import plistlib

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

def bump_marketing_version(project_path, level):
    # Specify the path to the project.pbxproj file
    pbxproj_path = project_path + '/project.pbxproj'

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

def bump_plist_default_value(plist_path, level):
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


# Example usage
project_path = './iOS/ITVHub_iOS.xcodeproj'
plist_path = './iOS/Settings/Settings.bundle/Root.plist'

level = 'minor'  # Specify the level: 'major', 'minor', or 'patch'

bump_marketing_version(project_path, level)
bump_plist_default_value(plist_path, level)

project_path = './tvOS/ITVHub_tvOS.xcodeproj'
bump_marketing_version(project_path, level)