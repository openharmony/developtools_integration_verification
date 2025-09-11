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


def monitor_file_and_stop(shell_script_path, target_file, shell_args=None, check_interval=1, 
                         use_shell=False):

    if isinstance(shell_args, str):
        command = [shell_script_path] + shlex.split(shell_args)
    elif shell_args:
        command = [shell_script_path] + shell_args
    else:
        command = [shell_script_path]
    
    command += ["--build-only-gn"]

    execute_build_command(command, use_shell=use_shell)
    
    file_detected = False

    while True:
        if os.path.exists(target_file):
            file_detected = True
            break
        sleep(0.5)

    if file_detected:
        if os.stat(target_file).st_size == 0:
            print("No changes to the unittest detected, skipping compilation directly.")
            sys.exit()
        command.remove("--build-only-gn")
        command.extend(["--build-target", "precise_module_build"])
        print(command)
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
        gns = []
        cs = []
        hs = []
        for key, value in change_info.items():
            print(value)
            changed_files = value.get("changed_file_list", {})
            print(changed_files)
            for op, processor in file_operations.items():
                if op in changed_files:
                    print(processor(changed_files[op]))
                    for modified_file in processor(changed_files[op]):
                        if modified_file.endswith(".h"):
                            hs.append("//" + os.path.join(key, modified_file))
                        elif modified_file.endswith(".gn"):
                            gns.append("//" + os.path.join(key, modified_file))
                        elif modified_file.endswith(".c") or modified_file.endswith(".cpp"):
                            cs.append("//" + os.path.join(key, modified_file))
        modified_files = {
            "h_file":hs,
            "c_file":cs,
            "gn_file":gns,
            "gn_module":[]
        }
        print(modified_files)
        with open('modify_files.json', 'w') as json_file:
            json.dump(modified_files, json_file, indent=4)
        return (
            [os.path.join(self.ace_root, f) for f in change_files],
            openharmony_fields
        )


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
    parser.add_argument('-f', '--file', required=True,
                        help='the path of the target file to be monitored')
    
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='file check interval time (seconds)')
    parser.add_argument('--use-shell', action='store_true',
                        help='execute commands using the shell (handle complex commands)')
    
    parser.add_argument('shell_args', nargs=argparse.REMAINDER,
                        help='parameters passed to the shell script (after --)')
    
    args = parser.parse_args()
    process_changes()
    shell_args = []
    if args.shell_args:
        try:
            sep_index = args.shell_args.index("--")
            shell_args = args.shell_args[sep_index + 1:]
        except ValueError:
            shell_args = args.shell_args
    
    success = monitor_file_and_stop(
        shell_script_path=args.script,
        target_file=args.file,
        shell_args=shell_args,
        check_interval=args.interval,
        use_shell=args.use_shell,
    )
    exit(0 if success else 1)
