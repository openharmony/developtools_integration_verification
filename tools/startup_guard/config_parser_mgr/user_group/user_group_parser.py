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

    def loadFile(self, fileName):
        #print(" loadFile %s" % fileName)
        if not os.path.exists(fileName):
            return
        try:
            with open(fileName, encoding='utf-8') as fp:
                line = fp.readline()
                while line :
                    if line.startswith("#") or len(line) < 3:
                        line = fp.readline()
                        continue
                    groupInfo = line.strip("\n").split(":")
                    if len (groupInfo) < 3:
                        line = fp.readline()
                        continue
                    self._handleGroupInfo(groupInfo)
                    line = fp.readline()
        except:
            pass

    def dump(self):
        for group in self._group.values() :
            print(str(group))

    def _handleGroupInfo(self, groupInfo):
        name = groupInfo[0].strip()
        userNames = name
        if len(groupInfo) > 3 and len(groupInfo[3]) > 0:
            userNames = groupInfo[3]
        oldGroup = self._group.get(name)
        if oldGroup:
            return
        group = {
            "name" : name,
            "groupId" : int(groupInfo[2], 10),
            "userNames" : userNames
        }
        self._group[name] = group

class PasswdFileParser():
    def __init__(self):
        self._passwd = {}
        self._passwd_yellow = {}
        self._name_list = []
        self._uid_list = []

    def loadFile(self, fileName):
        # print(" loadFile %s" % fileName)
        if not os.path.exists(fileName):
            return
        try:
            with open(fileName, encoding='utf-8') as fp:
                line = fp.readline()
                while line :
                    if line.startswith("#") or len(line) < 3:
                        line = fp.readline()
                        continue
                    passwdInfo = line.strip("\n").split(":")
                    if len (passwdInfo) < 4:
                        line = fp.readline()
                        continue
                    self._handlePasswdInfo(passwdInfo)
                    line = fp.readline()
        except:
            pass

    def dump(self):
        for group in self._passwd.values() :
            print(str(group))

    def _handlePasswdInfo(self, passwdInfo):
        name = passwdInfo[0].strip()
        self._uid_list.append(int(passwdInfo[2], 10))
        self._name_list.append(name)
        oldPasswd = self._passwd.get(name)
        if oldPasswd:
            return
        
        gid = int(passwdInfo[3], 10)
        uid = int(passwdInfo[2], 10)

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
    parser.loadFile(os.path.join(path, "system/etc/group"))
    #parser.dump()

    passwd = PasswdFileParser()
    passwd.loadFile(os.path.join(path, "system/etc/passwd"))
    # passwd.dump()
    return parser, passwd

if __name__ == '__main__':
    args_parser = _create_arg_parser()
    options = args_parser.parse_args()
    create_user_group_parser(options.input)

