#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

# This file is for get the mapping relationship of subsystem_name/component_name
# and their directory. The code is from Yude Chen.

import logging
import copy
import os
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import *
from pprint import pprint
import preprocess
from pkgs.gn_common_tool import GnVariableParser
from pkgs.simple_yaml_tool import SimpleYamlTool
from pkgs.basic_tool import BasicTool


_config = SimpleYamlTool.read_yaml("config.yaml")
"""
===============info handlers===============
"""


def extension_handler(paragraph: Text):
    return GnVariableParser.string_parser("output_extension", paragraph).strip('"')


def hap_name_handler(paragraph: Text):
    return GnVariableParser.string_parser("hap_name", paragraph).strip('"')


def target_type_handler(paragraph: Text):
    tt = GnVariableParser.string_parser("target_type", paragraph).strip('"')
    return tt


"""
===============gn lineno collector===============
"""


def gn_lineno_collect(match_pattern: str, project_path: str) -> DefaultDict[str, List[int]]:
    """
    在整个项目路径下搜索有特定target类型的BUILD.gn
    :param match_pattern: 进行grep的pattern，支持扩展的正则
    :param project_path: 项目路径（搜索路径）
    :return: {gn_file: [line_no_1, line_no_2, ..]}
    """
    black_list = _config.get("black_list")
    tbl = [x for x in black_list if os.sep in x]

    def handler(content: Text) -> List[str]:
        t = list(filter(lambda y: len(y) > 0, list(
            map(lambda x: x.strip(), content.split("\n")))))
        for item in tbl:
            p = os.path.join(project_path, item)
            t = list(filter(lambda x: p not in x, t))
        return t

    grep_list = BasicTool.grep_ern(match_pattern, path=project_path,
                                   include="BUILD.gn", exclude=tuple(black_list), post_handler=handler)
    gn_line_dict: DefaultDict[str, List[int]] = defaultdict(list)
    for gl in grep_list:
        gn_file, line_no, _ = gl.split(":")
        gn_line_dict[gn_file].append(line_no)
    return gn_line_dict


"""
===============target name parser===============
"""


class TargetNameParser:
    @classmethod
    def single_parser(cls, paragraph: Text) -> str:
        """
        查找类似shared_library("xxx")这种括号内只有一个参数的target的名称
        :param paragraph: 要解析的段落
        :return: target名称，如果是变量，不会对其进行解析
        """
        return BasicTool.re_group_1(paragraph, r"\w+\((.*)\)")

    @classmethod
    def second_parser(cls, paragraph: Text) -> str:
        """
        查找类似target("shared_library","xxx")这种的target名称（括号内第二个参数）
        :param paragraph: 要解析的段落
        :return: target名称，如果是变量，不会的其进行解析
        """
        return BasicTool.re_group_1(paragraph, r"\w+\(.*?, *(.*?)\)")


"""
===============post handlers===============
"""


class BasePostHandler(ABC):
    @abstractmethod
    def run(self, unit: Dict[str, AnyStr]) -> str:
        ...

    def __call__(self, unit: Dict[str, AnyStr]) -> str:
        return self.run(unit)


def add_prefix(content: str, prefix: str) -> str:
    if content and (not content.startswith(prefix)):
        return prefix+content
    return content


def add_postfix(content: str, postfix: str) -> str:
    if content and (not content.endswith(postfix)):
        return content+postfix
    return content


class DefaultPostHandler(BasePostHandler):
    def run(self, unit: Dict[str, AnyStr]):
        return unit["output_name"]


class HAPPostHandler(BasePostHandler):
    """
    for ohos_hap"""

    def run(self, unit: Dict[str, AnyStr]):
        extension = _config.get("default_extension").get("app")
        gn_hap_name = unit.get("hap_name")
        if gn_hap_name:
            return add_postfix(gn_hap_name, extension)
        return unit["output_name"]+extension


class SOPostHandler(BasePostHandler):
    """
    for shared_library"""

    def run(self, unit: Dict[str, AnyStr]):
        output_name = unit["output_name"]
        prefix = _config.get("default_prefix").get("shared_library")
        if unit.get("extension"):
            extension = unit.get("extension")
        else:
            extension = _config.get("default_extension").get("shared_library")
        if not extension.startswith('.'):
            extension = '.'+extension
        output_name = add_postfix(output_name, extension)
        return add_prefix(output_name, prefix)


class APostHandler(BasePostHandler):
    """
    for static library"""

    def run(self, unit: Dict[str, AnyStr]):
        output_name = unit["output_name"]
        prefix = _config.get("default_prefix").get("static_library")
        extension: str = _config.get("default_extension").get("static_library")
        if not extension.startswith('.'):
            extension = '.'+extension
        output_name = add_postfix(output_name, extension)
        return add_prefix(output_name, prefix)


class LiteLibPostHandler(BasePostHandler):
    """
    for lite_library"""

    def run(self, unit: Dict[str, AnyStr]):
        tp = unit["real_target_type"]
        output_name = unit["output_name"]
        if tp == "static_library":
            prefix = _config.get("default_prefix").get("static_library")
            extension = _config.get("default_extension").get("static_library")
        elif tp == "shared_library":
            prefix = _config.get("default_prefix").get("shared_library")
            extension = _config.get("default_extension").get("shared_library")
        else:
            prefix = str()
            extension = str()
        if extension and (not extension.startswith('.')):
            extension = '.'+extension
        output_name = add_postfix(output_name, extension)
        return add_prefix(output_name, prefix)


class LiteComponentPostHandler(BasePostHandler):
    """
    for lite_component"""

    def run(self, unit: Dict[str, AnyStr]):
        tp = unit["real_target_type"]
        output_name = unit["output_name"]
        extension = unit.get("output_extension")
        if tp == "shared_library":
            prefix = _config.get("default_prefix").get("shared_library")
            extension = _config.get("default_extension").get("shared_library")
        else:
            if tp != "executable":
                unit["description"] = "virtual node"
            prefix = str()
            extension = str()
        if extension and (not extension.startswith('.')):
            extension = '.'+extension
        output_name = add_postfix(output_name, extension)
        return add_prefix(output_name, prefix)


class TargetPostHandler(BasePostHandler):
    """
    for target(a,b){}"""

    def run(self, unit: Dict[str, AnyStr]):
        ...


def LiteLibS2MPostHandler(unit: Dict, result_dict: Dict) -> None:
    rt = unit.get("real_target_type")
    new_unit = copy.deepcopy(unit)
    if rt == "shared_library":
        new_unit["real_target_type"] = "static_library"
        k = LiteLibPostHandler()(new_unit)
        new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_unit
    elif rt == "static_library":
        new_unit["real_target_type"] = "shared_library"
        k = LiteLibPostHandler()(new_unit)
        new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_unit
    else:
        new_unit["real_target_type"] = "shared_library"
        k = LiteLibPostHandler()(new_unit)
        new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_unit

        new_new_unit = copy.deepcopy(unit)
        new_new_unit["real_target_type"] = "static_library"
        k = LiteLibPostHandler()(new_new_unit)
        new_new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_new_unit


def TargetS2MPostHandler(unit: Dict, result_dict: Dict) -> None:
    unit["description"] = "may not exist"
    tmp_a = copy.deepcopy(unit)
    tmp_a["real_target_type"] = "static_library"
    k = LiteLibPostHandler()(tmp_a)
    result_dict["target"][k] = tmp_a

    tmp_s = copy.deepcopy(unit)
    tmp_s["real_target_type"] = "shared_library"
    k = LiteLibPostHandler()(tmp_s)
    result_dict["target"][k] = tmp_s
