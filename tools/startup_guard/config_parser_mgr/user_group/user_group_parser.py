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

import string
import sys
import os

class GroupFileParser():
    def __init__(self):
        self._group = {}

    def load_file(self, file_name):
        if not os.path.exists(file_name):
            return
        try:
            with open(file_name, encoding='utf-8') as fp:
                line = fp.readline()
                while line :
                    if line.startswith("#") or len(line) < 3:
                        line = fp.readline()
                        continue
                    group_info = line.strip("\n").split(":")
                    if len (group_info) < 3:
                        line = fp.readline()
                        continue
                    self._handle_group_info(group_info)
                    line = fp.readline()
        except:
            pass

    def dump(self):
        for group in self._group.values() :
            print(str(group))

    def _handle_group_info(self, group_info):
        name = group_info[0].strip()
        user_names = name
        if len(group_info) > 3 and len(group_info[3]) > 0:
            user_names = group_info[3]
        old_group = self._group.get(name)
        if old_group:
            return
        group = {
            "name" : name,
            "groupId" : int(group_info[2], 10),
            "user_names" : user_names
        }
        self._group[name] = group

class PasswdFileParser():
    def __init__(self):
        self._passwd = {}
        self._passwd_yellow = {}
        self._name_list = []
        self._uid_list = []

    def load_file(self, file_name):
        if not os.path.exists(file_name):
            return
        try:
            with open(file_name, encoding='utf-8') as fp:
                line = fp.readline()
                while line :
                    if line.startswith("#") or len(line) < 3:
                        line = fp.readline()
                        continue
                    passwd_info = line.strip("\n").split(":")
                    if len (passwd_info) < 4:
                        line = fp.readline()
                        continue
                    self._handle_passwd_info(passwd_info)
                    line = fp.readline()
        except:
            pass

    def dump(self):
        for group in self._passwd.values() :
            print(str(group))

    def _handle_passwd_info(self, passwd_info):
        name = passwd_info[0].strip()
        self._uid_list.append(int(passwd_info[2], 10))
        self._name_list.append(name)
        old_passwd = self._passwd.get(name)
        if old_passwd:
            return
        
        gid = int(passwd_info[3], 10)
        uid = int(passwd_info[2], 10)

        passwd = {
            "name" : name,
            "groupId" : gid,
            "passwdId" : uid
        }
        self._passwd[name] = passwd

def _create_arg_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Collect group information from system/etc/group dir.')
    parser.add_argument('-i', '--input',
                        help='input group files base directory example "out/rk3568/packages/phone/" ', required=True)

    parser.add_argument('-o', '--output',
                        help='output group information database directory', required=False)
    return parser

def create_user_group_parser(base_path):
    path = os.path.join(base_path, "packages/phone")
    parser = GroupFileParser()
    parser.load_file(os.path.join(path, "system/etc/group"))

    passwd = PasswdFileParser()
    passwd.load_file(os.path.join(path, "system/etc/passwd"))
    return parser, passwd

if __name__ == '__main__':
    args_parser = _create_arg_parser()
    options = args_parser.parse_args()
    create_user_group_parser(options.input)

