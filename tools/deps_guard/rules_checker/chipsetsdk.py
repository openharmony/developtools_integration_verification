#!/usr/bin/env python
#coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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
import json

from .base_rule import BaseRule


class ChipsetSDKRule(BaseRule):
    RULE_NAME = "ChipsetSDK"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self.__out_path = mgr.get_product_out_path()
        self.__white_lists = self.load_chipsetsdk_json("chipsetsdk_info.json")
        self.__ignored_tags = ["platformsdk", "sasdk", "platformsdk_indirect", "ndk"]
        self.__valid_mod_tags = ["llndk", "chipsetsdk", "chipsetsdk_indirect", "chipsetsdk_sp", 
                                 "chipsetsdk_sp_indirect", "passthrough"] + self.__ignored_tags

    def get_sofile_list(self):
        return self.__white_lists

    def get_out_path(self):
        return self.__out_path

    def load_chipsetsdk_json(self, name):
        rules_dir = []
        if self._args and self._args.rules:
            self.log("****add more chipsetsdk info in:{}****".format(self._args.rules))
            rules_dir = rules_dir + self._args.rules

        chipsetsdk_rules_path = self.get_out_path().replace("out", "out/products_ext")
        new_rule_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../rules")
        if os.path.exists(chipsetsdk_rules_path):
            rules_dir.append(chipsetsdk_rules_path)
            self.log("****add more chipsetsdk info in dir:{}****".format(chipsetsdk_rules_path))
        elif os.path.exists(new_rule_path):
            rules_dir.append(new_rule_path)
            self.log("****add chipsetsdk_rules_path path:{}****".format(new_rule_path))
        res = []
        for d in rules_dir:
            rules_file = os.path.join(d, self.__class__.RULE_NAME, name)
            if os.path.isfile(rules_file):
                res = self.__parser_rules_file(rules_file, res)
            else:
                self.warn("****rules path not exist: {}****".format(rules_file))        
        
        return res

    def check(self):
        self.__load_chipsetsdks()
        self.__load_chipsetsdk_indirects()
        white_lists = self.get_dep_whitelist()

        # Check if all chipset modules depends on chipsetsdk modules only
        passed = self.__check_tags_correctly()
        self.log(f"****check_depends_on_chipsetsdk result:{passed}****")
        if not passed:
            return passed
        
        passed = self.check_if_deps_correctly(
            self.__modules_with_chipsetsdk_tag, ["chipsetsdk"] + self.__ignored_tags, self.__valid_mod_tags, white_lists)
        self.log(f"****check_if_deps_correctly result:{passed}****")
        if not passed:
            return passed
        
        passed = self.check_if_deps_correctly(
            self.__modules_with_chipsetsdk_indirect_tag, ["chipsetsdk_indirect"] + self.__ignored_tags, self.__valid_mod_tags, white_lists)
        self.log(f"****check_if_deps_correctly indirect result:{passed}****")
        if not passed:
            return passed
        
        passed = self.__check_if_tagged_correctly()
        self.log(f"****check_tagged_correctly result:{passed}****")
        if not passed:
            return passed

        self.__write_innerkits_header_files()

        return True

    def __parser_rules_file(self, rules_file, res):
        try:
            self.log("****Parsing rules file in {}****".format(rules_file))
            with open(rules_file, "r") as f:
                contents = f.read()
            if not contents:
                self.log("****rules file {} is null****".format(rules_file))
                return res
            json_data = json.loads(contents)
            for so in json_data:
                so_file_name = so.get("so_file_name")
                if so_file_name and so_file_name not in res:
                    res.append(so_file_name)
        except (FileNotFoundError, IOError, UnicodeDecodeError) as file_open_or_decode_err:
            self.error(file_open_or_decode_err)
        
        return res

    def __is_chipsetsdk_tagged(self, mod):
        if not "innerapi_tags" in mod:
            return False
        if "chipsetsdk" in mod["innerapi_tags"]:
            return True
        return False

    def __is_chipsetsdk_indirect(self, mod):
        if not "innerapi_tags" in mod:
            return False
        if "chipsetsdk_indirect" in mod["innerapi_tags"]:
            return True
        return False

    def __write_innerkits_header_files(self):
        inner_kits_info = os.path.join(self.get_mgr().get_product_out_path(), 
                                       "build_configs/parts_info/inner_kits_info.json")
        with open(inner_kits_info, "r") as f:
            info = json.load(f)

        headers = []
        for sdk in self.__chipsetsdk_mods:
            path = sdk["labelPath"][:sdk["labelPath"].find(":")]
            target_name = sdk["labelPath"][sdk["labelPath"].find(":") + 1:]
            item = {"name": sdk["componentName"] + ":" + target_name, "so_file_name":
                    sdk["name"], "path": sdk["labelPath"], "headers": []}
            if sdk["componentName"] not in info:
                headers.append(item)
                continue

            for name, innerapi in info[sdk["componentName"]].items():
                if innerapi["label"] != sdk["labelPath"]:
                    continue
                got_headers = True
                base = innerapi["header_base"]
                for f in innerapi["header_files"]:
                    item["headers"].append(os.path.join(base, f))
            headers.append(item)

        try:
            with os.fdopen(os.open(os.path.join(self.get_mgr().get_product_images_path(),
                                                "chipsetsdk_info.json"),
                                    os.O_WRONLY | os.O_CREAT, 0o644), "w") as f:
                json.dump(headers, f, indent=4)
        except FileNotFoundError as e:
            pass

        return headers

    def __check_tags_correctly(self):
        lists = self.get_dep_whitelist()

        passed = True

        self.__chipsetsdk_mods = []
        self.__all_mods = []
        self.__all_paths = {}
        self.__modules_with_chipsetsdk_tag = []
        self.__modules_with_chipsetsdk_indirect_tag = []

        # Check if any napi modules has dependedBy
        for mod in self.get_mgr().get_all():
            # Collect all modules with chipsetsdk tag
            if self.__is_chipsetsdk_tagged(mod):
                self.__modules_with_chipsetsdk_tag.append(mod)

            # Collect all modules with chipsetsdk_indirect tag
            if self.__is_chipsetsdk_indirect(mod):
                self.__modules_with_chipsetsdk_indirect_tag.append(mod)

            # Check chipset modules only
            if mod["path"].startswith("system"):
                continue

            # If callee is chipset module, it is OK
            if not mod["path"].endswith(".so"):
                continue

            self.__all_mods.append(mod["name"])
            self.__all_paths[mod["name"]] = mod["path"]
            
            # Check if all chipsetsdk/chisetsdk_indirect module are tagged correctly
            if "chipset-sdk/" in mod["path"]:
                if mod["name"] not in self.__chipsetsdks and mod["name"] not in self.__indirects:
                    print(json.dumps({
                        "name": f"{mod['componentName']}:{mod['moduleName']}",
                        "so_file_name": mod["name"],
                        "path": mod['labelPath'],
                        "headers": []
                    }),end="\n")
                    # Not allowed
                    passed = False
                    self.error("NEED MODIFY: so file %s in %s should be add in file chipsetsdk_info.json or chipsetsdk_indirect_info.json"
                            % (mod["name"], mod["labelPath"]))
                    continue

            # Check chipset modules depends
            for dep in mod["deps"]:
                callee = dep["callee"]

                # If callee is chipset module, it is OK
                if not callee["path"].startswith("system"):
                    continue

                # Add to list
                if callee not in self.__chipsetsdk_mods:
                    if "hdiType" not in callee or callee["hdiType"] != "hdi_proxy":
                        self.__chipsetsdk_mods.append(callee)

                # If callee is chipset module, it is OK
                if not callee["path"].endswith(".so"):
                    continue

                # If callee is in Chipset SDK white list module, it is OK
                if callee["name"] in lists:
                    continue

                # If callee is asan library, it is OK
                if callee["name"].endswith(".asan.so"):
                    continue

                # If callee is hdi proxy module, it is OK
                if "hdiType" in callee and callee["hdiType"] == "hdi_proxy":
                    continue

        return passed

    def __check_if_tagged_correctly(self):
        passed = True
        modules_with_chipsetsdk_tags = [mod["name"] for mod in self.__modules_with_chipsetsdk_tag]
        indirect_tags = [mod["name"] for mod in self.__modules_with_chipsetsdk_indirect_tag]

        for mod in self.__chipsetsdks:
            if mod not in self.__all_mods:
                continue
            if mod in self.__all_paths:
                if "chipset-sdk/" not in self.__all_paths[mod]:
                    continue
            if mod not in modules_with_chipsetsdk_tags:
                passed = False
                self.error('Chipset SDK module %s in chipsetsdk_info.json should add innerapi_tags with "chipsetsdk"'
                          % mod)

        for mod in self.__indirects:
            if mod not in self.__all_mods:
                continue
            if mod in self.__all_paths:
                if "chipset-sdk/" not in self.__all_paths[mod]:
                    continue
            if mod not in indirect_tags:
                passed = False
                self.error('chipsetsdk_indirect module %s in chipsetsdk_indirect_info.json should add innerapi_tags "chipsetsdk_indirect"'
                          % mod)

        return passed

    def __load_chipsetsdks(self):
        self.__chipsetsdks = self.load_chipsetsdk_json("chipsetsdk_info.json")

    def __load_chipsetsdk_indirects(self):
        self.__indirects = self.load_chipsetsdk_json("chipsetsdk_indirect.json")
