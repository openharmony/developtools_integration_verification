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
import psutil
import sys
import re
import tempfile
import shutil
import json

def find_python_child_processes(parent_pid):
    python_processes = []
    try:
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            try:
                cmdline = child.cmdline()
                if cmdline and ('python' in cmdline[0].lower() or any('python' in part.lower() for part in cmdline)):
                    python_processes.append(child)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return python_processes

def kill_python_child_processes(parent_pid):
    python_processes = find_python_child_processes(parent_pid)
    for proc in python_processes:
        try:
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    time.sleep(0.5)
    
    for proc in python_processes:
        try:
            if proc.is_running():
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def kill_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        for child in children:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        gone, alive = psutil.wait_procs(children, timeout=5)
        
        for child in alive:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        try:
            parent.terminate()
            parent.wait(5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except psutil.TimeoutExpired:
            try:
                parent.kill()
            except:
                pass
    
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

def get_target(target):
    if target.startswith("//"):
        return target[2:]
    else:
        return target

def execute_build_command(command, targets=None, use_shell=False):
    if targets:
        if len(targets) > 1000:
            temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
            temp_file.write(targets)
            temp_file.close()
            
            command.append(f"@{temp_file.name}")
            cleanup_file = temp_file.name
        else:
            command.append(targets)
            cleanup_file = None
    else:
        cleanup_file = None
    
    try:
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
        print(f"构建完成，退出码: {return_code}")
        return return_code == 0
    
    finally:
        if cleanup_file and os.path.exists(cleanup_file):
            os.unlink(cleanup_file)

def monitor_file_and_stop(shell_script_path, target_file, shell_args=None, check_interval=1, 
                         use_shell=False, timeout=None):

    if isinstance(shell_args, str):
        command = [shell_script_path] + shlex.split(shell_args)
    elif shell_args:
        command = [shell_script_path] + shell_args
    else:
        command = [shell_script_path]
    
    process = subprocess.Popen(
        command,
        shell=use_shell,
        text=True,
        start_new_session=True
    )
    
    pid = process.pid
    
    start_time = time.time()
    last_dot_time = start_time
    file_detected = False
    terminate_manually = False
    
    try:
        while True:
            current_time = time.time()
            
            if os.path.exists(target_file):
                print(f"\n检测到目标文件已生成: {target_file}")
                file_detected = True
                terminate_manually = True
                break
                
            if process.poll() is not None:
                if os.path.exists(target_file):
                    file_detected = True
                break

            if timeout and (current_time - start_time) > timeout:
                terminate_manually = True
                break

            if current_time - last_dot_time > 1.0:
                print(".", end="", flush=True)
                last_dot_time = current_time
            
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        terminate_manually = True
    
    finally:
        if terminate_manually:
            kill_process_tree(pid)
            
            wait_attempts = 0
            while wait_attempts < 5 and psutil.pid_exists(pid):
                time.sleep(0.5)
                wait_attempts += 1
            
            if psutil.pid_exists(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except:
                    pass
        else:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                kill_process_tree(pid)
    
    if file_detected:
        
        time.sleep(1)
        
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
                        help='显示帮助信息并退出')
    
    parser.add_argument('-s', '--script', required=True, 
                        help='要执行的shell脚本路径')
    parser.add_argument('-f', '--file', required=True,
                        help='要监控的目标文件路径')
    
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='文件检查间隔时间（秒）')
    parser.add_argument('-t', '--timeout', type=float, default=None,
                        help='最大等待时间（秒）')
    parser.add_argument('--use-shell', action='store_true',
                        help='使用shell执行命令（处理复杂命令）')
    
    parser.add_argument('shell_args', nargs=argparse.REMAINDER,
                        help='传递给shell脚本的参数（在--之后）')
    
    args = parser.parse_args()
    process_changes()
    shell_args = []
    if args.shell_args:
        try:
            sep_index = args.shell_args.index("--")
            shell_args = args.shell_args[sep_index + 1:]
        except ValueError:
            shell_args = args.shell_args
    
    try:
        import psutil
    except ImportError:
        exit(1)
    
    success = monitor_file_and_stop(
        shell_script_path=args.script,
        target_file=args.file,
        shell_args=shell_args,
        check_interval=args.interval,
        use_shell=args.use_shell,
        timeout=args.timeout
    )
    exit(0 if success else 1)
