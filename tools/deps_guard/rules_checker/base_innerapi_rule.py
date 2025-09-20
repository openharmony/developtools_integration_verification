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


class BaseInnerapiRule(BaseRule):
    RULE_NAME = "BaseInnerApi"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self.__ignored_tags = ["platformsdk", "sasdk", "platformsdk_indirect", "ndk"]
        self.__valid_system_tags = ["llndk", "chipsetsdk", "chipsetsdk_indirect", "chipsetsdk_sp"
                                    "chipsetsdk_sp_indirect", "passthrough"] + self.__ignored_tags
        self.__valid_vendor_tags = ["llndk", "chipsetsdk", "chipsetsdk_sp", "llndk", "passthrough",
                                   "passthrough_indirect"] + self.__ignored_tags

    def is_only(self, ignored_tags, mod):
        if mod["name"].endswith(".so") or mod["name"].endswith(".so.1"):
            if mod["path"].startswith("system"):
                return "system"
            else:
                return "vendor"
        else:
            return ""

    def check(self):
        passed = True
        white_lists = self.get_dep_whitelist()

        for mod in self.get_mgr().get_all():
            innerapi_tags = mod["innerapi_tags"]
            # mod is system only scene
            if self.is_only(self.__ignored_tags, mod) == "system" and \
                    all(item in self.__valid_system_tags for item in innerapi_tags):
                for dep in mod["deps"]:
                    callee = dep["callee"]
                    callee_innerapi_tags = callee["innerapi_tags"]
                    if self.is_only(self.__ignored_tags, callee) == "system" or \
                        (callee_innerapi_tags and all(item in self.__valid_system_tags for item in callee_innerapi_tags)) or \
                            callee["name"] in white_lists:
                        continue
                    else:
                        self.error("NEED MODIFY: system only module %s depends on wrong module as %s in %s, dep module path is %s" 
                                   %(mod["name"], callee["name"], mod["labelPath"], callee["path"]))
                        passed = False
            # mod is vendor only scene
            elif self.is_only(self.__ignored_tags, mod) == "vendor" and \
                    all(item in self.__valid_vendor_tags for item in innerapi_tags):
                for dep in mod["deps"]:
                    callee = dep["callee"]
                    callee_innerapi_tags = callee["innerapi_tags"]
                    if self.is_only(self.__ignored_tags, callee) == "vendor" or \
                            (callee_innerapi_tags and all(item in self.__valid_vendor_tags for item in callee_innerapi_tags)) or \
                            callee["name"] in white_lists:
                        continue
                    else:
                        self.error("NEED MODIFY: vendor only module %s depends on wrong module as %s in %s, dep module path is %s" 
                                   %(mod["name"], callee["name"], mod["labelPath"], callee["path"]))
                        passed = False
        return passed
