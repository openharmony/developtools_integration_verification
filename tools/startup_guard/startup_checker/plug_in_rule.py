#!/usr/bin/env python
#coding=utf-8

#
# Copyright (c) 2024 Huawei Device Co., Ltd.
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

from .base_rule import BaseRule

class PlugInModuleRule(BaseRule):
    RULE_NAME = "NO-Plug-In_Module-Init"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self._base_so = []
        self._private_so = {}
        self._passwd = True

    def _read_elf_dt_needed(self, file):
        # print(file)
        paser = self._private_so
        file_name = os.path.basename(file)
        proc = subprocess.Popen(["readelf", "-d", file],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = proc.communicate()
        lines = out.splitlines()
        for line in lines:
            line = str(line)
            if " (NEEDED) " in line:
                needed = line.strip().split("[")[-1].split("]")[0]
                for key, item in paser.items():
                    if file_name == key :
                        if needed in item["deps"] or needed in self._base_so:
                            pass
                        else:
                            self._passwd = False
                            error_log = "the dependent shared library {} of {} is not in whitelist".format(needed, file_name) 
                            self.error("%s" % error_log)
                            continue
                        pass


    def check_plug_in_library(self):
        cfg_parser = self.get_mgr().get_parser_by_name('config_parser')
        white_lists =self.get_white_lists()
        for key, item in white_lists[0].items():
            if key == "base_library":
                self._base_so = item
            if key == "private_library":
                self._private_so = item 
        keys = list(self._private_so.keys())
        for name in cfg_parser._plug_in:
            if os.path.basename(name) not in keys:
                self.error("%s is not in whitelists" % os.path.basename(name))
                self._passwd = False
                continue
            self._read_elf_dt_needed(name)
        return self._passwd
        
    def __check__(self):
        return self.check_plug_in_library()
