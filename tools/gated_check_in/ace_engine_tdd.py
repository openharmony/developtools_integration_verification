# -*- coding: utf-8 -*-
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


import os
import re
import json
import mmap
from functools import lru_cache
from collections import defaultdict


class BuildProcessor:
    
    def __init__(self, root_dir, ace_root):
        self.root_dir = root_dir
        self.ace_root = ace_root
        self.build_info = defaultdict(lambda: {"name": "", "source_list": [], "deps_list": [], "include_list": [], "config_list": []})
        self.data_json = []
        self.group_json = []
        
        self.unittest_pattern = re.compile(
            r'(ace|ohos)_unittest\("([^"]*)"\)\s*\{(.*?)(?=\})',
            re.DOTALL | re.MULTILINE
        )
        self.group_pattern = re.compile(
            r'group\("([^"]*)"\)\s*\{(.*?)(?=\})',
            re.DOTALL | re.MULTILINE
        )
        self.sources_pattern = re.compile(r'sources\s*=\s*\[(.*?)\]', re.DOTALL)
        self.deps_pattern = re.compile(r'deps\s*[+]?=\s*\[(.*?)\]', re.DOTALL)
        self.includes_pattern = re.compile(r'include_dirs\s*[+]?=\s*\[(.*?)\]', re.DOTALL)
        self.configs_pattern = re.compile(r'configs\s*[+]?=\s*\[(.*?)\]', re.DOTALL)
    
    def execute(self):
        for root, _, files in os.walk(self.root_dir):
            if "BUILD.gn" in files:
                path = os.path.join(root, "BUILD.gn")
                self.parse_build_gn(path)
                self.parse_groups(path)
        
        change_files, oh_fields = self.process_changes()
        
        if len(oh_fields) == 1 and oh_fields[0] == "arkui_ace_engine":
            print(" ".join(self.analyze_impact(change_files)))
        else:
            print(f"TDDarkuarkui_ace_engine")
        self.generate_output()

    def parse_build_gn(self, file_path):
        content = self._read_file(file_path)
        processed_content = "\n".join(line.split("#")[0].rstrip() 
                                    for line in content.splitlines())
        
        for match in self.unittest_pattern.finditer(processed_content):
            self._process_unittest(match, file_path)

    def process_file(self, file_path):
        content = self._read_file(file_path)
        return {header for line in content.split('\n') 
                if (header := self._process_includes(line))}

    def parse_groups(self, file_path):
        content = self._read_file(file_path)
        processed_content = "\n".join(line.split("#")[0].rstrip() 
                                    for line in content.splitlines())
        
        for match in self.group_pattern.finditer(processed_content):
            self._process_group(match, file_path)

    def process_changes(self):
        change_info = self._read_json("change_info.json")
        openharmony_fields = [v["name"] for v in change_info.values() if "name" in v]
        
        change_files = []
        file_operations = {
            "added": lambda x: x,
            "rename": lambda x: [item for pair in x for item in pair],
            "modified": lambda x: x,
            "deleted": lambda x: x
        }
        
        for value in change_info.values():
            changed_files = value.get("changed_file_list", {})
            for op, processor in file_operations.items():
                if op in changed_files:
                    change_files.extend(processor(changed_files[op]))
        
        return (
            [os.path.join(self.ace_root, f) for f in change_files],
            openharmony_fields
        )

    def generate_output(self):
        with open("test_targets.json", "w") as f:
            json.dump(self.data_json, f, indent=2)
            
        with open("groups.json", "w") as f:
            json.dump(self.group_json, f, indent=2)

    def analyze_impact(self, change_files):
        tdd_data = self._read_json("developtools/integration_verification/tools/gated_check_in/ace_engine.json") or {}
        adapted_targets = set(tdd_data.get("adapted_test_targets", []))
        adapting_targets = set(tdd_data.get("adapting_test_targets", []))
        
        change_set = set(change_files)
        impacted = []
        
        for target in self.data_json:
            target_sets = {
                "source_list": set(target["source_list"]),
                "deps_list": set(target["deps_list"]),
                "includes_list": set(target["includes_list"]),
                "configs_list": set(target["configs_list"]),
                "source_h": set(target["source_h"]),
                "dep_h": set(target["dep_h"]),
                "includes_h": set(target["includes_h"]),
                "configs_h": set(target["configs_h"])
            }
            if any(change_set & s for s in target_sets.values()):
                impacted.append(target["test_target"])
                if target["test_target"] in adapting_targets:
                    return ["TDDarkui_ace_engine"]
        
        return ["TDDarkui_ace_engine"] if not impacted else impacted

    @lru_cache(maxsize=128)
    def _read_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return ""

    def _process_includes(self, line):
        for pattern in [r'#include\s*"(.*?)"', r'#include\s*<(.*?)>']:
            match = re.match(pattern, line)
            if match and (header := match.group(1)).endswith('.h'):
                return header
        return None

    def _process_unittest(self, match, file_path):
        target_name = match.group(2)
        target_content = match.group(3)
        base_path = os.path.dirname(file_path)
        
        sources = self._get_gn_content(self.sources_pattern, target_content, base_path)
        deps = self._get_gn_content(self.deps_pattern, target_content, base_path)
        includes = self._get_gn_content(self.includes_pattern, target_content, base_path)
        configs = self._get_gn_content(self.configs_pattern, target_content, base_path)
        
        source_h = {h for s in sources for h in self.process_file(s)}
        dep_h = {h for d in deps for h in self.process_file(d)}
        include_h = {h for s in includes for h in self.process_file(s)}
        config_h = {h for d in configs for h in self.process_file(d)}
        
        build_target = f"{os.path.dirname(file_path)}:{target_name}"
        self.data_json.append({
            "test_target": build_target,
            "source_list": sources,
            "deps_list": deps,
            "includes_list": includes,
            "configs_list": configs,
            "source_h": list(source_h),
            "dep_h": list(dep_h),
            "includes_h": list(include_h),
            "configs_h": list(config_h)
        })

    def _process_group(self, match, file_path):
        group_name = match.group(1)
        group_content = match.group(2)
        base_path = os.path.dirname(file_path)
        
        deps = [self._normalize_path(d, base_path).replace("/:", ":")
                for d in self._get_gn_content(self.deps_pattern, group_content, "")]
        
        self.group_json.append({
            "group_name": f"{base_path}:{group_name}",
            "deps_list": deps
        })

    def _get_gn_content(self, pattern, content, base_path):
        if not (match := pattern.search(content)):
            return []
        return [self._normalize_path(s, base_path) 
                for s in match.group(1).split(',') if s.strip()]

    def _normalize_path(self, s, base_path):
        s = s.strip().strip('"')
        if '/' not in s:
            return os.path.join(base_path, s)
        return s.replace('$ace_root', self.ace_root)

    def _read_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {}

    

if __name__ == "__main__":
    processor = BuildProcessor(
        root_dir="foundation/arkui/ace_engine",
        ace_root="foundation/arkui/ace_engine"
    )
    processor.execute()

