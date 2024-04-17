#!/usr/bin/env python
#coding=utf-8

#
# Copyright (c) 2023-2024 Huawei Device Co., Ltd.
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


class CmdRule(BaseRule):
    RULE_NAME = "NO-Config-Cmds-In-Init"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self._cmds = {}
        self._start_modes = {}
        self._boot_list = {}
        self._condition_list = {}
        self._start_cmd_list = {}

    def __check__(self):
        return self.check_config_cmd()

    def check_config_cmd(self):
        passed = True
        self._parse_while_list()
        cfg_parser = self.get_mgr().get_parser_by_name('config_parser')
        self._get_json_service()

        start_passed = self._check_start_cmd(cfg_parser)
        secon_passed = self._check_selinux(cfg_parser)
        cmd_passed = self._check_cmdline_in_parser(cfg_parser)
        start_mode_passed = self._check_service(cfg_parser)
        passed = start_passed and secon_passed and cmd_passed and start_mode_passed
        return passed

    def _get_json_service(self):
        for _, start_mode in enumerate(self._start_modes):
            if start_mode.get("start-mode") == "boot":
                self._boot_list = start_mode.get("service")
            elif start_mode.get("start-mode") == "condition":
                self._condition_list = start_mode.get("service")  
        pass

    def _get_start_cmds(self, parser):
        lists = {}
        for cmd in parser._cmds:
            if cmd["name"] == "start":
                lists[cmd["content"]] = cmd["fileId"]
                pass
        return lists

    def _parse_while_list(self):
        white_lists = self.get_white_lists()[0]
        for key, item in white_lists.items():
            if key == "cmds":
                self._cmds = item
            if key == "start-modes":
                self._start_modes = item
            if key == "start-cmd":
                self._start_cmd_list = item

    def _check_condition_start_mode(self, cmd_list, service_name, passed):
        if service_name in self._condition_list and service_name in cmd_list:
            pass
        else:
            self.warn("\'%s\' cannot be started in conditional mode" % service_name)
        return passed


    def _check_service(self, parser):
        boot_passed = True
        condition_passed = True
        start_cmd_list = self._get_start_cmds(parser).keys()
        for key, item in parser._services.items(): 
            if item.get("start_mode") == "boot":
                if key not in self._boot_list:
                    self.warn("\'%s\' cannot be started in boot mode" % key)
            elif item.get("on_demand") is not True and item.get("start_mode") == "condition":
                condition_passed = self._check_condition_start_mode(start_cmd_list, key, condition_passed)
        return boot_passed and condition_passed

    def _check_file_id_in_cmds(self, cmdlist, cmdline):
        file_id_list = set()
        for _, cmd in enumerate(cmdlist):
            if cmdline == cmd["name"]:
                file_id_list.add(cmd["fileId"])
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
                    output = "\'{}\' is timeout command, in {}".format(cmd["cmd"], key)
                    self.error("%s" % str(output))
                    passed = False
            file_id_list.clear()
        return passed

    def _check_selinux(self, parser):
        if parser._selinux != 'enforcing':
            self.warn("selinux status is %s" % parser._selinux)
            return True

        passed = True
        for key, item in parser._services.items():
            if item.get("secon") == "":
                output_str = "%s \'secon\' is empty" % key
                self.error("%s" % str(output_str))
                passed = False
        return passed

    def _check_start_cmd(self, parser):
        passed = True
        start_cmd_list = self._get_start_cmds(parser)
        for cmd, file_id in start_cmd_list.items():
            if cmd in list(self._start_cmd_list):
                pass
            else:
                for key, item in parser._files.items():
                    if item["fileId"] == file_id:
                        log_str = "{} is not in start cmd list. path:{}".format(cmd, item["file_name"])
                        self.warn("%s" % log_str)
                        passed = False
                    pass
        return passed
