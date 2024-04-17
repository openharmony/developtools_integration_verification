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

from .base_rule import BaseRule

class UserGroupModuleRule(BaseRule):
    RULE_NAME = "NO-User-Group_In-Init"

    def __init__(self, mgr, args):
        super().__init__(mgr, args)

    def __check__(self):
        return self.check_user_group()

    def check_user_group(self):
        passed = True
        passwd_parser = self.get_mgr().get_parser_by_name('user_group')
        group_id = passwd_parser[0]
        passwd_id = passwd_parser[1]
        
        repeat_name = []
        repeat_uid = []
        for uid in passwd_id._uid_list:
            if passwd_id._uid_list.count(uid) > 1:
                repeat_uid.append(uid)

        for name in passwd_id._name_list:
            if passwd_id._name_list.count(name) > 1:
                repeat_name.append(name)
        if len(repeat_name):
            passed = False
            self.error("repeat uid name list:  %s" % repeat_name)

        if len(repeat_uid):
            passed = False
            self.error("repeat uid value list:  %s" % repeat_uid)

        if (self._check_gid_in_passwd(passwd_id._passwd) == -1):
            passed = False
            self.error("%s has different passwd and group values" % value["uid"])

    def _check_gid_in_passwd(self, passwd):
        is_passed = True
        for key, value in passwd.items():    
            if value["passwdId"] == value["groupId"]:
                pass
            else:
                is_passed = False
                self.error("%s has different passwd and group values" % value["name"])
        return is_passed
