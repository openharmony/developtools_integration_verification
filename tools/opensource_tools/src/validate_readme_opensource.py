# src/validate_readme_opensource.py

import os
import json
import argparse

REQUIRED_FIELDS = [
    "Name",
    "License",
    "License File",
    "Version Number",
    "Owner",
    "Upstream URL",
    "Description"
]

def validate_readme_opensource(file_path):
    """
    验证 README.OpenSource 文件的格式和内容。

    :param file_path: README.OpenSource 文件路径
    :return: 是否验证通过，错误信息列表
    """
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            errors.append("The file does not contain a JSON array.")
            return False, errors

        for idx, component in enumerate(data):
            for field in REQUIRED_FIELDS:
                if field not in component:
                    errors.append(f"Component {idx + 1} is missing required field: {field}")
    except json.JSONDecodeError as e:
        errors.append(f"JSON decode error: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
        return False, errors

    return len(errors) == 0, errors

def main():
    parser = argparse.ArgumentParser(description='Validate README.OpenSource files.')
    parser.add_argument('directory', help='Directory to search for README.OpenSource files.')
    args = parser.parse_args()

    for root, dirs, files in os.walk(args.directory):
        if 'README.OpenSource' in files:
            file_path = os.path.join(root, 'README.OpenSource')
            valid, errors = validate_readme_opensource(file_path)
            if valid:
                print(f"{file_path} is valid.")
            else:
                print(f"{file_path} is invalid:")
                for error in errors:
                    print(f"  - {error}")

if __name__ == '__main__':
    main()

