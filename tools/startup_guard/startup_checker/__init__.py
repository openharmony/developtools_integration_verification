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

from .cmds_rule import CmdRule
from .system_parameter_rules import SystemParameterRule
from .user_group_rule import UserGroupModuleRule
from .plug_in_rule import PlugInModuleRule

def check_all_rules(mgr, args):
    rules = [
        CmdRule,
        SystemParameterRule,
        UserGroupModuleRule,
        PlugInModuleRule,
    ]

    passed = True
    for rule in rules:
        r = rule(mgr, args)
        r.log("Do %s rule checking now:" % rule.RULE_NAME)
        if not r.__check__():
            passed = False
            r.log("  Please refer to: \033[91m%s\x1b[0m" % r.get_help_url())

    if args and args.no_fail:
        return True

    return passed
