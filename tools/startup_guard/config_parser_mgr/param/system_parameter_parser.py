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

class ParameterParser(dict):
    def __init__(self, prefix, parameter = None):
        self["prefix"] = prefix
        if parameter == None:
            self["type"] = "string"
            self["dacUser"] = ""
            self["dacGroup"] = ""
            self["dacMode"] = 0
            self["selinuxLabel"] = ""
            self["value"] = ""
        else:
            self["type"] = parameter.get("type")
            self["dacUser"] = parameter.get("dacUser")
            self["dacGroup"] = parameter.get("dacGroup")
            self["dacMode"] = parameter.get("dacMode")
            self["selinuxLabel"] = parameter.get("selinuxLabel")
            self["value"] = parameter.get("value")

    def decode(self, info):
        self["value"] = info.strip("\"").strip("\'")
        #print("value '%s'" % self["value"])
        return True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "%s= DAC[%s:%s:%s] selinux[%s] value=%s" % (self["prefix"], self["dacUser"], self["dacGroup"], self["dacMode"], self["selinuxLabel"], self["value"])

class ParameterDacParser(ParameterParser):
    def __init__(self, prefix, parameter=None):
        ParameterParser.__init__(self, prefix, parameter)

    def decode(self, info):
        dacInfo = info.strip("\"").strip("\'").split(":")
        if len(dacInfo) < 3:
            print("Invalid dac %s" % info)
            return False

        self["dacUser"] = dacInfo[0]
        self["dacGroup"] = dacInfo[1]
        self["dacMode"] = dacInfo[2]
        if len(dacInfo) > 3:
            self["type"] = dacInfo[3]
        return True

class ParameterSelinuxParser(ParameterParser):
    def __init__(self, prefix, parameter=None):
        ParameterParser.__init__(self, prefix, parameter)

    def decode(self, info):
        self["selinuxLabel"] = info
        #print("name %s selinux %s" % (self["prefix"], info))
        return True

class ParameterFileParser():
    def __init__(self):
        self._parameters = {}

    def _handle_param_info(self, file_name, param_info):
        param_name = param_info[0].strip()
        old_param = self._parameters.get(param_name)
        if file_name.endswith(".para.dac"):
            param = ParameterDacParser(param_name, old_param)
            if (param.decode(param_info[2].strip())):
                self._parameters[param_name] = param
        elif file_name.endswith(".para"):
            param = ParameterParser(param_name, old_param)
            if (param.decode(param_info[2].strip())):
                self._parameters[param_name] = param
        else:
            param = ParameterSelinuxParser(param_name, old_param)
            if (param.decode(param_info[2].strip())):
                self._parameters[param_name] = param

    def load_parameter_file(self, file_name, str = "="):
        # print(" loadParameterFile %s" % fileName)
        try:
            with open(file_name, encoding='utf-8') as fp:
                line = fp.readline()
                while line :
                    #print("line %s" % (line))
                    if line.startswith("#") or len(line) < 3:
                        line = fp.readline()
                        continue
                    paramInfo = line.partition(str)
                    if len (paramInfo) != 3:
                        line = fp.readline()
                        continue
                    self._handle_param_info(file_name, paramInfo)
                    line = fp.readline()
        except:
            print("Error, invalid parameter file ", file_name)
            pass

    def dump_parameter(self):
        for param in self._parameters.values():
            print(str(param))

    def _check_file(self, file):
        valid_file_ext = [".para", ".para.dac"]
        if not file.is_file():
            return False
        for ext in valid_file_ext:
            if file.name.endswith(ext):
                return True
        return False

    def _scan_parameter_file(self, dir):
        if not os.path.exists(dir):
            return
        with os.scandir(dir) as files:
            for file in files:
                if self._check_file(file):
                    self.load_parameter_file(file.path)

    def scan_parameter_file(self, dir):
        parameter_paths = [
            "/system/etc/param/ohos_const",
            "/vendor/etc/param",
            "/chip_prod/etc/param",
            "/sys_prod/etc/param",
            "/system/etc/param",
        ]
        for path in parameter_paths:
            self._scan_parameter_file(dir + "/packages/phone" + path)

def __create_arg_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Collect parameter information from xxxx/etc/param dir.')
    parser.add_argument('-i', '--input',
                        help='input parameter files base directory example "out/rk3568/packages/phone/" ', required=True)
    return parser

def parameters_collect(base_path):
    parser = ParameterFileParser()
    parser.scan_parameter_file(base_path)
    parser.load_parameter_file(base_path + "/packages/phone/system/etc/selinux/targeted/contexts/parameter_contexts", " ")
    # parser.dumpParameter()
    return parser

if __name__ == '__main__':
    args_parser = __create_arg_parser()
    options = args_parser.parse_args()
    parameters_collect(options.input)
