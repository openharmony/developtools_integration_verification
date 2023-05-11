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

from .base_rule import BaseRule

class SystemParameterRule(BaseRule):
    RULE_NAME = "NO-Config-SystemParameter-In-INIT"

    def _check_param_name(self, param_name, empty_flag):
        # len: (0, 96]
        # Only allow alphanumeric, plus '.', '-', '@', ':', or '_'/
        # Don't allow ".." to appear in a param name 
        if len(param_name) > 96 or len(param_name) < 1 or param_name[0] == '.' or '..' in param_name:
            return False

        if empty_flag is False:
            if param_name[-1] == '.':
                return False

        if param_name == "#":
            return True

        for char_value in param_name:
            if char_value in '._-@:':
                continue

            if char_value.isalnum():
                continue
            return False
        return True

    def _check_Param_in_init(self):
        passed = True
        value_empty_flag = True
        white_list =self.get_white_lists()
        parser = self.get_mgr().get_parser_by_name('system_parameter_whitelist')
        for key, item in parser._parameters.items():
            if str(item)[-1] == "=":
                value_empty_flag = True
            else:
                value_empty_flag = False

            if not self._check_param_name(key, value_empty_flag):
                self.error("Invalid param: %s" % key)
                continue
            if key in white_list:
                continue
            self.error("%s is not found in the whitelist" % key)
            passed = False
        return passed
        
    def __check__(self):
        return self._check_Param_in_init()
