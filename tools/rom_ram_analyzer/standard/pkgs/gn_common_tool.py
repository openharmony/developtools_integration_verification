#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import os
import json
import re
from typing import *

if __name__ == '__main__':
    from basic_tool import BasicTool
else:
    from pkgs.basic_tool import BasicTool


class GnCommonTool:
    """
    处理BUILD.gn文件的通用方法
    """

    @classmethod
    def is_gn_variable(cls, target: str, has_quote: bool = True):
        """
        判断target是否是gn中的变量:
        规则：如果是有引号的模式，则没有引号均认为是变量，有引号的情况下，如有是"$xxx"的模式，则认为xxx是变量；如果是无引号模式，则只要$开头就认为是变量
        b = "xxx"
        c = b
        c = "${b}"
        "$p"
        """
        target = target.strip()
        if not has_quote:
            return target.startswith("$")
        if target.startswith('"') and target.endswith('"'):
            target = target.strip('"')
            if target.startswith("${") and target.endswith("}"):
                return True
            elif target.startswith("$"):
                return True
            return False
        else:
            return True

    # 给__find_variables_in_gn用的，减少io
    __var_val_mem_dict = dict()

    @classmethod
    def find_variables_in_gn(cls, var_name_tuple: tuple, path: str, stop_tail: str = "home") -> tuple:
        """
        同时查找多个gn变量的值
        var_name_tuple：变量名的tuple，变量名应是未经过处理后的，如：
        xxx
        "${xxx}"
        "$xxx"
        """

        if os.path.isfile(path):
            path = os.path.split(path)[0]
        var_val_dict = dict()
        not_found_count = len(var_name_tuple)
        for var in var_name_tuple:
            val = GnCommonTool.__var_val_mem_dict.get(var)
            if val is not None:
                not_found_count -= 1
            var_val_dict[var] = val
        while not path.endswith(stop_tail) and not_found_count != 0:
            for v in var_name_tuple:
                cmd = r"grep -Ern '^( *){} *= *\".*?\"' --include=*.gn* {}| grep -Ev '\$' | head -n 1 | grep -E '\".*\"' -wo".format(
                    v.strip('"').lstrip("${").rstrip('}'), path)
                output = os.popen(cmd).read().strip().strip('"')
                if len(output) != 0:
                    not_found_count -= 1
                    var_val_dict[v] = output
                    GnCommonTool.__var_val_mem_dict[v] = output
            path = os.path.split(path)[0]
        return tuple(var_val_dict.values())
    
    @classmethod
    def find_part_subsystem(cls, gn_file: str, project_path: str) -> tuple:
        """
        查找gn_file对应的part_name和subsystem
        如果在gn中找不到，就到bundle.json中去找
        """
        part_var_flag = False  # 标识这个变量从gn中取出的原始值是不是变量
        subsystem_var_flag = False
        var_list = list()
        part_name_pattern = r"part_name *=\s*\S*"
        subsystem_pattern = r"subsystem_name *=\s*\S*"
        meta_grep_pattern = "grep -E '{}' {} | head -n 1"
        part_cmd = meta_grep_pattern.format(part_name_pattern, gn_file)
        subsystem_cmd = meta_grep_pattern.format(subsystem_pattern, gn_file)

        part_name, subsystem_name = cls._parse_part_subsystem(part_var_flag, subsystem_var_flag,
                                                              var_list, part_cmd, subsystem_cmd, gn_file, project_path)
        if part_name and subsystem_name:
            return part_name, subsystem_name
        # 如果有一个没有找到，就要一层层去找bundle.json文件
        t_part_name, t_subsystem_name = cls.__find_part_subsystem_from_bundle(
            gn_file, stop_tail=project_path)
        if t_part_name:
            part_name = t_part_name
        if t_subsystem_name:
            subsystem_name = t_subsystem_name
        return part_name, subsystem_name

    @classmethod
    def __find_part_subsystem_from_bundle(cls, gnpath: str, stop_tail: str = "home") -> tuple:
        """
        根据BUILD.gn的全路径，一层层往上面查找bundle.json文件，
        并从bundle.json中查找part_name和subsystem
        """
        filename = "bundle.json"
        part_name = None
        subsystem_name = None
        if stop_tail not in gnpath:
            return part_name, subsystem_name
        if os.path.isfile(gnpath):
            gnpath = os.path.split(gnpath)[0]
        while not gnpath.endswith(stop_tail):
            bundle_path = os.path.join(gnpath, filename)
            if not os.path.isfile(bundle_path):  # 如果该文件不在该目录下
                gnpath = os.path.split(gnpath)[0]
                continue
            with open(bundle_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                try:
                    part_name = content["component"]["name"]
                    subsystem_name = content["component"]["subsystem"]
                except KeyError:
                    ...
                finally:
                    break
        part_name = None if (part_name is not None and len(
            part_name) == 0) else part_name
        subsystem_name = None if (subsystem_name is not None and len(
            subsystem_name) == 0) else subsystem_name
        return part_name, subsystem_name

    @classmethod
    def _parse_part_subsystem(cls, part_var_flag: bool, subsystem_var_flag: bool, var_list: List[str], part_cmd: str,
                              subsystem_cmd: str, gn_file: str, project_path: str) -> Tuple[str, str]:
        part_name = subsystem_name = None
        part = os.popen(part_cmd).read().strip()
        if len(part) != 0:
            part = part.split('=')[-1].strip()
            if GnCommonTool.is_gn_variable(part):
                part_var_flag = True
                var_list.append(part)
            else:
                part_name = part.strip('"')
                if len(part_name) == 0:
                    part_name = None
        subsystem = os.popen(subsystem_cmd).read().strip()
        if len(subsystem) != 0:  # 这里是只是看有没有grep到关键字
            subsystem = subsystem.split('=')[-1].strip()
            if GnCommonTool.is_gn_variable(subsystem):
                subsystem_var_flag = True
                var_list.append(subsystem)
            else:
                subsystem_name = subsystem.strip('"')
                if len(subsystem_name) == 0:
                    subsystem_name = None
        if part_var_flag and subsystem_var_flag:
            part_name, subsystem_name = GnCommonTool.find_variables_in_gn(
                tuple(var_list), gn_file, project_path)
        elif part_var_flag:
            t = GnCommonTool.find_variables_in_gn(
                tuple(var_list), gn_file, project_path)[0]
            part_name = t if t is not None and len(t) != 0 else part_name
        elif subsystem_var_flag:
            t = GnCommonTool.find_variables_in_gn(
                tuple(var_list), gn_file, project_path)[0]
            subsystem_name = t if t is not None and len(
                t) != 0 else subsystem_name
        return part_name, subsystem_name


class GnVariableParser:
    @classmethod
    def string_parser(cls, var: str, content: str) -> str:
        """
        解析值为字符串的变量,没有对引号进行去除,如果是a = b这种b为变量的,则无法匹配
        :param content: 要进行解析的内容
        :param var: 变量名
        :return: 变量值[str]
        """
        result = BasicTool.re_group_1(
            content, r"{} *= *[\n]?(\".*?\")".format(var), flags=re.S | re.M)
        return result

    @classmethod
    def list_parser(cls, var: str, content: str) -> List[str]:
        """
        解析值为列表的变量，list的元素必须全为数字或字符串,且没有对引号进行去除,如果是a = b这种b为变量的,则无法匹配
        :param var: 变量名
        :param content: 要进行
        :return: 变量值[List]
        """
        result = BasicTool.re_group_1(
            content, r"{} *= *(\[.*?\])".format(var), flags=re.S | re.M)
        result_list = list()
        for item in result.lstrip('[').rstrip(']').split('\n'):
            item = item.strip().strip(',"')
            if not item:
                continue
            result_list.append(item)
        return result_list
