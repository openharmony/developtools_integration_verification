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


ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


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


def monitor_file_and_stop(shell_script_path, target_file, shell_args=None, 
                         use_shell=False):

    if isinstance(shell_args, str):
        command = [shell_script_path] + shlex.split(shell_args)
    elif shell_args:
        command = [shell_script_path] + shell_args
    else:
        command = [shell_script_path]
    
    command += ["--build-only-gn", "--no-prebuilt-sdk"]

    execute_build_command(command, use_shell=use_shell)
    
    file_detected = False

    while True:
        if os.path.exists(target_file):
            file_detected = True
            break
        time.sleep(0.5)

    if file_detected:
        if os.stat(target_file).st_size == 0:
            print("No changes to the unittest detected, skipping compilation directly.")
            sys.exit()
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
        "h": h_files,
        "hh": h_files,
        "hpp": h_files,
        "gn": gn_files,
        "gni": gn_files,
        "c": c_files,
        "cpp": c_files,
        "cc": c_files,
        "cxx": c_files,
        "js": c_files,
        "ets": c_files,
        "in": h_files,
        "cl": h_files,
        "cppm": h_files,
        "cuh": h_files,
        "def": h_files,
        "gch": h_files,
        "glsl": h_files,
        "h++": h_files,
        "hhu": h_files,
        "hlsl": h_files,
        "i": h_files,
        "icc": h_files,
        "impl": h_files,
        "inl": h_files,
        "ipp": h_files,
        "ixx": h_files,
        "mpp": h_files,
        "mxx": h_files,
        "pch": h_files,
        "protp": h_files,
        "swig": h_files,
        "template": h_files,
        "tcc": h_files,
        "thrift": h_files,
        "tpp": h_files,
        "wgsl": h_files,
    }
    
    for key, value in change_info.items():
        changed_files = value.get("changed_file_list", {})
        for operation, processor in file_operations.items():
            if operation not in changed_files:
                print(f"unknown file operation: {operation}")
                continue                
            for modified_file in processor(changed_files[operation]):
                target_list = file_type_map.get(get_file_extension(modified_file), other_files)
                if target_list == gn_files:
                    patch_file_content = generate_patch(os.path.join(ROOT_PATH, key), value.get("name"))
                    print(patch_file_content)
                    review_content = parse_patch_for_buildgn(patch_file_content)
                    print("-"*100)
                    print(review_content)
                    print(ROOT_PATH)
                    print("-"*100)
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
    return (
        [os.path.join(self.ace_root, f) for f in change_files],
        openharmony_fields
    )


def parse_patch_for_buildgn(content):
    """
    解析patch文件，提取BUILD.gn文件的修改行号
    
    特别注意：
    1. 只提取以'+'开头的行（新增行）
    2. 对于添加空行的情况，也要正确识别
    """
    
    # 查找所有BUILD.gn文件的diff块
    buildgn_diffs = re.findall(
        r'diff --git a/(.*?BUILD\.gn.*?) b/(.*?BUILD\.gn.*?)\n(.*?)(?=\ndiff --git|\Z)',
        content,
        re.DOTALL
    )
    
    if not buildgn_diffs:
        return None
    
    results = []
    
    for old_file, new_file, diff_content in buildgn_diffs:
        changed_lines = []
        current_line_num = 0
        
        # 解析diff内容
        lines = diff_content.split('\n')
        
        for line in lines:
            # 查找行号信息
            if line.startswith('@@'):
                # 提取新文件起始行号
                match = re.search(r'\+(\d+)(?:,(\d+))?', line)
                if match:
                    current_line_num = int(match.group(1))
                continue
            
            # 如果是新增行（但不包括文件头）
            if line.startswith('+') and not line.startswith('++'):
                changed_lines.append(str(current_line_num))
                current_line_num += 1
                continue
            
            # 如果是上下文行或删除行，行号递增（但删除行不计入修改）
            if line.startswith(' ') or line.startswith('-'):
                if not line.startswith('---') and not line.startswith('--'):
                    current_line_num += 1
        
        if changed_lines:
            results.append(f"{new_file} {','.join(changed_lines)}")
    
    return results


def generate_patch(part_path, part_name):
    original_cwd = os.getcwd()
    patch_file = ""
    patch_content = ""
    try:
        os.chdir(part_path)  
        # 生成patch文件名
        repo_name = part_name
        patch_file = f"{repo_name}.patch"
            
        cmd = f"git format-patch HEAD^ --stdout"
            
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
                
            # 将输出写入patch文件
            if result.stdout.strip():
                patch_content = result.stdout
                with open(patch_file, 'w', encoding='utf-8') as pf:
                    pf.write(result.stdout)
            else:
                print(f"  nothing change，no patch file")
                    
        except subprocess.CalledProcessError as e:
            print(f"  git diff command shibai: {e}")
            print(f"  generate patch error: {e.stderr}")
                
    except Exception as e:
        print(f"  generate patch error: {e}")
    finally:
        os.chdir(original_cwd)
    return patch_content



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
    parser.add_argument('-f', '--file', required=True,
                        help='the path of the target file to be monitored')
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
        use_shell=args.use_shell,
    )

    exit(0 if success else 1)

