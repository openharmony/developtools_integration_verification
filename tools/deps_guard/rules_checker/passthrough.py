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


class PassthroughRule(BaseRule):
    RULE_NAME = "Passthrough"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self.__out_path = mgr.get_product_out_path()
        self.__white_lists = self.load_passthrough_json("passthrough_info.json")
        self.__ignored_tags = ["platformsdk", "sasdk", "platformsdk_indirect", "ndk"]
        self.__valid_mod_tags = ["llndk", "chipsetsdk_sp", "passthrough", "passthrough_indirect"] + self.__ignored_tags

    def get_white_lists(self):
        return self.__white_lists

    def get_out_path(self):
        return self.__out_path

    def load_passthrough_json(self, name):
        rules_dir = []
        if self._args and self._args.rules:
            self.log("****add more passthrough info in:{}****".format(self._args.rules))
            rules_dir = rules_dir + self._args.rules

        chipsetsdk_rules_path = self.get_out_path().replace("out", "out/products_ext")
        new_rule_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../rules")
        if os.path.exists(chipsetsdk_rules_path):
            self.log("****add more passthrough info in dir:{}****".format(chipsetsdk_rules_path))
            rules_dir.append(chipsetsdk_rules_path)
        elif os.path.exists(new_rule_path):
            self.log("****add more passthrough info in dir:{}****".format(new_rule_path))
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
        self.__load_passthroughs()
        self.__load_passthrough_indirects()
        white_lists = self.get_dep_whitelist()

        # Check if all chipset modules depends on chipsetsdk modules only
        passed = self.__check_depends_on_passthrough()
        self.log(f"****check_depends_on_passthrough result:{passed}****")
        if not passed:
            return passed
        
        passed = self.check_if_deps_correctly(
            self.__modules_with_passthrough_tag, ["passthrough"] + self.__ignored_tags, self.__valid_mod_tags, white_lists)
        self.log(f"****check_if_deps_correctly result:{passed}****")
        if not passed:
            return passed
        
        passed = self.check_if_deps_correctly(
            self.__modules_with_passthrough_indirect_tag, ["passthrough_indirect"] + self.__ignored_tags, self.__valid_mod_tags, white_lists)
        self.log(f"****check_if_deps_correctly indirect result:{passed}****")
        if not passed:
            return passed
        
        passed = self.__check_if_tagged_correctly()
        self.log(f"****check_tagged_correctly result:{passed}****")
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

    def __is_passthrough_tagged(self, mod):
        if not "innerapi_tags" in mod:
            return False
        if "passthrough" in mod["innerapi_tags"]:
            return True
        return False

    def __is_passthrough_indirect(self, mod):
        if not "innerapi_tags" in mod:
            return False
        if "passthrough_indirect" in mod["innerapi_tags"]:
            return True
        return False

    def __check_depends_on_passthrough(self):
        passed = True

        self.__modules_with_passthrough_tag = []
        self.__modules_with_passthrough_indirect_tag = []
        self.__all_mods = []

        # Check if any napi modules has dependedBy
        for mod in self.get_mgr().get_all():
            # Collect all modules with passthrough tag
            if self.__is_passthrough_tagged(mod):
                self.__modules_with_passthrough_tag.append(mod)

            # Collect all modules with passthrough_indirect tag
            if self.__is_passthrough_indirect(mod):
                self.__modules_with_passthrough_indirect_tag.append(mod)

            # Check passthrough so only
            if not mod["path"].endswith("so"):
                continue

            self.__all_mods.append(mod["name"])

            if "passthrough" in mod["path"] and "passthrough/indirect" not in mod["path"]:
                if mod["name"] not in self.__passthroughs:
                    # Not allowed
                    passed = False
                    self.error("NEED MODIFY: so file %s in %s should be add in file passthrough_info.json"
                            % (mod["name"], mod["labelPath"]))
                    continue

            if "passthrough/indirect" in mod["path"]:
                if mod["name"] not in self.__indirects:
                    # Not allowed
                    passed = False
                    self.error("NEED MODIFY: so file %s in %s should be add in file passthrough_indirect_info.json"
                            % (mod["name"], mod["labelPath"]))
                    continue

        return passed

    def __check_if_tagged_correctly(self):
        passed = True
        passthrough_tags = [mod["name"] for mod in self.__modules_with_passthrough_tag]
        indirect_tags = [mod["name"] for mod in self.__modules_with_passthrough_indirect_tag]

        for mod in self.__passthroughs:
            if mod not in self.__all_mods:
                continue
            if mod not in passthrough_tags:
                passed = False    
                self.error('Passthrough module %s in passthrough_info.json should add innerapi_tags with "passthrough"'
                          % mod)

        for mod in self.__indirects:
            if mod not in self.__all_mods:
                continue
            if mod not in indirect_tags:
                passed = False
                self.error('passthrough_indirect module %s in passthrough_indirect_info.json should add innerapi_tags "passthrough_indirect"'
                          % mod)

        return passed

    def __load_passthroughs(self):
        self.__passthroughs = self.load_passthrough_json("passthrough_info.json")

    def __load_passthrough_indirects(self):
        self.__indirects = self.load_passthrough_json("passthrough_indirect.json")
