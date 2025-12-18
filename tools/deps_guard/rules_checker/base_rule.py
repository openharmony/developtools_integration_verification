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


class BaseRule(object):
    RULE_NAME = ""

    def __init__(self, mgr, args):
        self._mgr = mgr
        self._args = args
        self.__white_lists = self.load_files("whitelist.json")
        self.__out_path = mgr.get_product_out_path()
        self.__base_sofiles = ["libc.so", "libutils.z.so", "ld-musl-aarch64.so.1", "libconfiguration.z.so", "libusbmanager.z.so",
                               "libsms.z.so"]
    def load_files(self, name):
        rules_dir = []
        rules_dir.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../rules"))
        if self._args and self._args.rules:
            rules_dir = rules_dir + self._args.rules

        res = []
        for d in rules_dir:
            rules_file = os.path.join(d, self.__class__.RULE_NAME, name)
            try:
                with open(rules_file, "r") as f:
                    jsonstr = "".join([line.strip() for line in f if not line.strip().startswith("//")])
                    res = res + json.loads(jsonstr)
            except:
                pass

        return res

    def get_mgr(self):
        return self._mgr

    def get_white_lists(self):
        return self.__white_lists

    def log(self, info):
        print(info)

    def warn(self, info):
        print("\033[35m[WARNING]\x1b[0m: %s" % info)

    def error(self, info):
        print("\033[91m[NOT ALLOWED]\x1b[0m: %s" % info)

    def get_help_url(self):
        return "https://gitee.com/openharmony/developtools_integration_verification/tree/master/tools/deps_guard/rules/%s/README.md" % self.__class__.RULE_NAME
    
    def get_out_path(self):
        return self.__out_path

    def is_only(self, mod):
        vendor_paths = ["vendor/", "updater_vendor/", "chip_prod/", "eng_chipset/", "log/", "userdata/"]
        system_paths = ["system/", "updater/", "ramdisk/", "eng_system/", "patch/", "updater_ramdisk/"]

        innerapi_tags = ["llndk", "chipsetsdk", "chipsetsdk_indirect", "chipsetsdk_sp", "chipsetsdk_sp_indirect", 
                         "passthrough", "passthrough_indirect"]
        is_system = False
        is_vendor = False
    
        if not (mod["name"].endswith(".so") or mod["name"].endswith(".so.1")):
            return "other"
    
        mod_path = mod["path"]
        for system_path in system_paths:
            if system_path in mod_path:
                is_system = True
                break
        for vendor_path in vendor_paths:
            if vendor_path in mod_path:
                is_vendor = True
                break
    
        mod_innerapi_tags = mod["innerapi_tags"]
        if all(item not in mod_innerapi_tags for item in innerapi_tags):
            if is_system:
                return "system"
            elif is_vendor:
                return "vendor"
            else:
                return "other"
        else:
            return "other"   
 
    def get_dep_whitelist(self):   
        whitelist_file = os.path.join(self.get_out_path().replace("out", "out/products_ext"), "chipsetsdk_dep_whitelist.json")
        if not os.path.exists(whitelist_file):
            whitelist_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), f"../rules/chipsetsdk_dep_whitelist.json")
        res = []
        if os.path.exists(whitelist_file):
            self.log("****chipsetsdk dep whitelist file is {}****".format(whitelist_file))
            with open(whitelist_file, "r") as f:
                contents = f.read()
            if not contents:
                self.log("****system/vendor only whitelist.json {} is null****".format(whitelist_file))
            json_data = json.loads(contents)
            for so in json_data:
                so_file_name = so.get("so_file_name")
                dep_file_name = so.get("dep_file_name")
                so_dict = {so_file_name: dep_file_name}
                if so_dict not in res:
                    res.append(so_dict)

        return res

    # To be override
    def check(self):
        # Default pass
        return True

    def check_if_deps_correctly(self, check_modules, valid_mod_tags, valid_dep_tags, white_lists):
        # check if mod and callee have wrong innerapi tags
        passed = True
        for mod in check_modules:
            innerapi_tags = mod["innerapi_tags"]
            if innerapi_tags and all(item in valid_mod_tags for item in innerapi_tags):
                for dep in mod["deps"]:
                    callee = dep["callee"]

                    if callee["name"] in self.__base_sofiles:
                        continue

                    if "duplicate" in callee.keys() and callee["duplicate"]:
                        passed = False
                        self.error("NEED MODIFY: %s has the same name in other package path, sofile name should be modified" % (callee["name"]))

                    dep_innerapi_tags = callee["innerapi_tags"]
                    wrong_tags = [item for item in dep_innerapi_tags if item not in valid_dep_tags]

                    in_whitelist = False
                    for so_dict in white_lists:
                        for k, v in so_dict.items():
                            if k == mod["name"] and v == callee["name"]:
                                in_whitelist = True
                                break

                    if in_whitelist:
                        continue
                    
                    # llndk can dep system only sofile
                    if "system" in valid_dep_tags and self.is_only(callee) == "system":
                        continue

                    # check system/vendor only
                    if self.is_only(callee) == "system":
                        passed = False
                        self.error("NEED MODIFY: %s with innerapi_tags [%s] cannot depend system only file %s with %s" 
                            % (mod["name"], ",".join(innerapi_tags), callee["name"], callee["labelPath"]))
                    elif self.is_only(callee) == "vendor":
                        passed = False
                        self.error("NEED MODIFY: %s with innerapi_tags [%s] cannot depend vendor only file %s with %s" 
                            % (mod["name"], ",".join(innerapi_tags), callee["name"], callee["labelPath"]))

                    if dep_innerapi_tags and all(item in valid_dep_tags for item in dep_innerapi_tags):
                        continue
                    elif not dep_innerapi_tags:
                        continue

                    passed = False
                    self.error("NEED MODIFY: %s with innerapi_tags [%s] has dep file %s with %s contains wrong dep innerapi_tags [%s] in innerapi_tags [%s]" 
                        % (mod["name"], ",".join(innerapi_tags), callee["name"], callee["labelPath"], ",".join(wrong_tags), ",".join(dep_innerapi_tags)))
            else:
                wrong_tags = [item for item in innerapi_tags if item not in valid_mod_tags]
                self.error("NEED MODIFY: module %s with %s contains wrong mod innerapi_tags [%s] in innerapi_tags [%s]" 
                           % (mod["name"], mod["path"], ",".join(wrong_tags), ",".join(innerapi_tags)))
                return False

        return passed
