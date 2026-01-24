 # -*- coding: utf-8 -*-

#
# Copyright (c) 2025 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import subprocess
import time
import argparse
import shlex
import signal
import sys
import re
import tempfile
import shutil
import json


def get_target(target):
    if target.startswith("//"):
        return target[2:]
    else:
        return target


def execute_build_command(command, use_shell=False):
    process = subprocess.Popen(
        command,
        shell=use_shell,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
        
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
        
    return_code = process.poll()
    print(f"build finish，return code is: {return_code}")
    return return_code == 0


def monitor_file_and_stop(shell_script_path, shell_args=None, 
                         use_shell=False, bundles=[]):

    if isinstance(shell_args, str):
        command = [shell_script_path] + shlex.split(shell_args)
    elif shell_args:
        command = [shell_script_path] + shell_args
    else:
        command = [shell_script_path]
    
    command += ["--build-only-gn", "--no-prebuilt-sdk"]

    #execute_build_command(command, use_shell=use_shell)
    
    file_detected = True 

    '''
    while True:
        if os.path.exists(target_file):
            file_detected = True
            break
        time.sleep(0.5)
        '''
    build_arkui = False
    for bundle in bundles:
        if "arkui" in bundle:
            build_arkui = True
            break
    
    if not build_arkui:
        command = [
            'ohos_precise_config=developtools/integration_verification/tools/precise_build/precise_build_tdd_config.json'
            if c == 'ohos_precise_config=developtools/integration_verification/tools/precise_build/precise_build_tdd_test_config.json'
            else c for c in command
            ]

    if file_detected:
        '''
        if os.stat(target_file).st_size == 0:
            print("No changes to the unittest detected, skipping compilation directly.")
            sys.exit()
        '''
        command.remove("--build-only-gn")
        command.remove("--no-prebuilt-sdk")
        command.extend(["--build-target", "precise_module_build"])
        return execute_build_command(command, use_shell=use_shell)
    
    return False


def process_changes():
    change_info = read_json("change_info.json")
    openharmony_fields = [v["name"] for v in change_info.values() if "name" in v]    
    change_files = []
    file_operations = {
        "added": lambda x: x,
        "rename": lambda x: [item for pair in x for item in pair],
        "modified": lambda x: x,
        "deleted": lambda x: x
    }
    gn_files, c_files, h_files, other_files = [], [], [], []
    file_type_map = {
        'h': h_files,
        'hh': h_files,
        'hpp': h_files,
        'gn': gn_files,
        'c': c_files,
        'cpp': c_files,
        'cc': c_files,
        'cxx': c_files,
        'js': c_files,
        'ets': c_files,
        'in': h_files,
        'cl': h_files,
        'cppm': h_files,
        'cuh': h_files,
        'def': h_files,
        'gch': h_files,
        'glsl': h_files,
        'h++': h_files,
        'hhu': h_files,
        'hlsl': h_files,
        'i': h_files,
        'icc': h_files,
        'impl': h_files,
        'inl': h_files,
        'ipp': h_files,
        'ixx': h_files,
        'mpp': h_files,
        'mxx': h_files,
        'pch': h_files,
        'protp': h_files,
        'swig': h_files,
        'template': h_files,
        'tcc': h_files,
        'thrift': h_files,
        'tpp': h_files,
        'wgsl': h_files,
    }
    

    bundles = []
    for key, value in change_info.items():
        changed_files = value.get("changed_file_list", {})
        bundles.append(key)
        for operation, processor in file_operations.items():
            if operation not in changed_files:
                print(f"unknown file operation: {operation}")
                continue                
            for modified_file in processor(changed_files[operation]):
                target_list = file_type_map.get(get_file_extension(modified_file), other_files)
                if target_list is not None:
                    target_list.append("//" + os.path.join(key, modified_file))

    modified_files = {
        "h_file": h_files,
        "c_file": c_files,
        "gn_file": gn_files,
        "other_file": other_files,
        "gn_module":[]
    }
    file_path = os.path.abspath(__file__)
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(file_path)))))
    write_file = os.path.join(root_path, "modify_files.json")
    with open(write_file, 'w') as json_file:
        json.dump(modified_files, json_file, indent=4)
    return bundles

def get_file_extension(filename):
    if '.' in filename:
        return filename.split(".")[-1]
    else:
        return None

def read_json(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )
    
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='display help information and exit')
    parser.add_argument('-s', '--script', required=True, 
                        help='the path to the shell script to be executed')
    #parser.add_argument('-f', '--file', required=True,
    #                    help='the path of the target file to be monitored')
    parser.add_argument('--use-shell', action='store_true',
                        help='execute commands using the shell (handle complex commands)')
    parser.add_argument('shell_args', nargs=argparse.REMAINDER,
                        help='parameters passed to the shell script (after --)')
    
    args = parser.parse_args()
    bundles = []
    bundles = process_changes()
    shell_args = []
    if args.shell_args:
        try:
            sep_index = args.shell_args.index("--")
            shell_args = args.shell_args[sep_index + 1:]
        except ValueError:
            shell_args = args.shell_args
    
    success = monitor_file_and_stop(
        shell_script_path=args.script,
        #target_file=args.file,
        shell_args=shell_args,
        use_shell=args.use_shell,
        bundles=bundles
    )

    exit(0 if success else 1)

