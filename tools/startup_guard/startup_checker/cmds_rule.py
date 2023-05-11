#!/usr/bin/env python
#coding=utf-8

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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

class cmdRule(BaseRule):
    RULE_NAME = "NO-Config-Cmds-In-Init"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self._cmds = {}
        self._start_modes = {}
        self._boot_list = {}
        self._condition_list = {}

    def _get_json_service(self):
        for i in range(len(self._start_modes)):
            if self._start_modes[i]["start-mode"] == "boot":
                self._boot_list = self._start_modes[i]["service"]
            elif self._start_modes[i]["start-mode"] == "condition":
                self._condition_list = self._start_modes[i]["service"]  
        pass

    def _get_start_cmds(self, parser):
        list = []
        for cmd in parser._cmds:
            if cmd["name"] == "start":
                list.append(cmd["content"])
                pass
        return list  

    def _parse_while_list(self):
        white_lists =self.get_white_lists()[0]
        for key, item in white_lists.items():
            if key == "cmds":
                self._cmds = item
            if key == "start-modes":
                self._start_modes = item

    def _check_condition_start_mode(self, cmd_list, service_name, passed):
        # print(cmd_list)
        if service_name in self._condition_list and service_name in cmd_list:
            pass
        else:
            self.error("\'%s\' cannot be started in conditional mode" % service_name)
            passed = False
        return passed


    def _check_service(self, parser):
        boot_passed = True
        condition_passed = True
        start_cmd_list = self._get_start_cmds(parser)
        for key, item in parser._services.items(): 
            if item.get("start_mode") == "boot":
                if key not in self._boot_list:
                    self.error("\'%s\' cannot be started in boot mode" % key)
                    boot_passed = False
            elif item.get("on_demand") is not True and item.get("start_mode") == "condition":
                condition_passed = self._check_condition_start_mode(start_cmd_list, key, condition_passed)
        return boot_passed and condition_passed

    def _check_file_id_in_cmds(self, cmdlist, cmdline):
        file_id_list = set()
        # print(cmdlist)
        for i in range(len(cmdlist)):
            if cmdline == cmdlist[i]["name"]:
                file_id_list.add(cmdlist[i]["fileId"])
                pass
        return file_id_list

    def _check_cmdline_in_parser(self, parser):
        passed = True
        cmdline = []
        file_id_list = set()
        parser_cmds = parser._cmds

        for cmd in self._cmds:
            cmdline = cmd["cmd"]
            file_id_list = self._check_file_id_in_cmds(parser_cmds, cmdline)
            file_lists = cmd["location"]
            for key, item in parser._files.items():
                if item["fileId"] in file_id_list and key not in file_lists:
                    output = "\'" + cmd["cmd"] + "\' is invalid, in "+  key
                    self.error("%s" % str(output))
                    passed = False
            file_id_list.clear()
        return passed

    def _check_selinux(self, parser):
        if parser._selinux != 'enforcing':
            self.warn("selinux status is %s" %parser._selinux)
            return False

        passed = True
        for key, item in parser._services.items():
            if item.get("secon") is None:
                output_str = "%s \'secon\' is empty" % key
                self.warn("%s" % str(output_str))
                passed = False
        return passed

    def check_config_cmd(self):
        self._parse_while_list()
        cfg_parser = self.get_mgr().get_parser_by_name('cmd_whitelist')
        self._get_json_service()
        self._get_start_cmds(cfg_parser)

        secon_passed = self._check_selinux(cfg_parser)
        cmd_passed = self._check_cmdline_in_parser(cfg_parser)
        start_mode_passed = self._check_service(cfg_parser)
        return secon_passed and cmd_passed and start_mode_passed

    def __check__(self):
        return self.check_config_cmd()
