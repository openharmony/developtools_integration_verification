#!/usr/bin/env python
#coding=utf-8

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
import json

from .base_rule import BaseRule


class LLndkRule(BaseRule):
    RULE_NAME = "LLndk"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self.__out_path = mgr.get_product_out_path()
        self.__white_lists = self.load_llndk_json("llndk_info.json")
        self.__ignored_tags = ["platformsdk", "sasdk", "platformsdk_indirect", "ndk"]
        self.__valid_mod_tags = ["llndk", "passthrough"] + self.__ignored_tags

    def get_white_lists(self):
        return self.__white_lists

    def get_out_path(self):
        return self.__out_path

    def load_llndk_json(self, name):
        rules_dir = []
        if self._args and self._args.rules:
            self.log("****add more llndk info in:{}****".format(self._args.rules))
            rules_dir = rules_dir + self._args.rules

        llndk_rules_path = self.get_out_path().replace("out", "out/products_ext")
        new_rule_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../rules")
        if os.path.exists(llndk_rules_path):
            self.log("****add more llndk info in dir:{}****".format(llndk_rules_path))
            rules_dir.append(llndk_rules_path)
        elif os.path.exists(new_rule_path):
            self.log("****add more llndk info in dir:{}****".format(new_rule_path))
            rules_dir.append(new_rule_path)
        res = []
        for d in rules_dir:
            rules_file = os.path.join(d, self.__class__.RULE_NAME, name)
            if os.path.isfile(rules_file):
                res = self.__parser_rules_file(rules_file, res)
            else:
                self.warn("****rules path not exist: {}****".format(rules_file))

        return res

    def check(self):
        self.__modules_with_llndk_tag = []
        self.__all_mods = []
        self.__all_paths = {}
        white_lists = self.get_dep_whitelist()
        self.__load_llndks()
        
        passed = True
        for mod in self.get_mgr().get_all():
            if self.__is_llndk_tagged(mod):
                self.__modules_with_llndk_tag.append(mod)
            
            self.__all_mods.append(mod["name"])
            self.__all_paths[mod["name"]] = mod["path"]

            if "llndk" in mod["path"] and "llndk" not in mod["innerapi_tags"]:
                # Not allowed
                self.error("NEED MODIFY: so file %s should add innerapi_tags llndk in %s"
                           % (mod["name"], mod["labelPath"]))
                passed = False
                continue
        if not passed:
            return passed

        # Check if all llndk modules are correctly tagged by innerapi_tags
        passed = self.__check_if_tagged_correctly()
        self.log(f"****check_if_tagged_correctly result:{passed}****")
        if not passed:
            return passed
        
        passed = self.check_if_deps_correctly(
            self.__modules_with_llndk_tag, self.__valid_mod_tags, self.__valid_mod_tags, white_lists)
        self.log(f"****check_if_deps_correctly result:{passed}****")
        if not passed:
            return passed

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

    def __is_llndk_tagged(self, mod):
        if not "innerapi_tags" in mod:
            return False
        if "llndk" in mod["innerapi_tags"]:
            return True
        return False

    def __check_if_tagged_correctly(self):
        passed = True
        llndk_tags = [mod["name"] for mod in self.__modules_with_llndk_tag]

        for mod in self.__llndks:
            if mod not in self.__all_mods:
                continue
            if mod in self.__all_paths:
                if "llndk/" not in self.__all_paths[mod]:
                    continue
            if mod not in llndk_tags:
                passed = False
                self.error('llndk module %s in llndk_info.json should add innerapi_tags with "llndk"' % mod)

        return passed

    def __load_llndks(self):
        self.__llndks = self.load_llndk_json("llndk_info.json")