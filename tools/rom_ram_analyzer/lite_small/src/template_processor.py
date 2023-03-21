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

# This file contains some template processor to collection information 
# from some gn's template in BUILD.gn

from typing import *
from abc import ABC, abstractmethod
import os
import logging
from pprint import pprint

from pkgs.basic_tool import do_nothing, BasicTool
from pkgs.gn_common_tool import GnCommonTool, GnVariableParser
from misc import *

TYPE = Literal["str", "list"]


class BaseProcessor(ABC):
    """
    extend and usage:
    DerivedClass(BaseProcessor):
        def call():
            # your implementation

    """

    def __init__(self,
                 project_path: str,
                 result_dict: Dict[str, Dict[str, Dict]],
                 target_type: str,
                 match_pattern: str,
                 sub_com_dict: Dict[str, Dict[str, str]],
                 target_name_parser: Callable[[Text], Text] = do_nothing,
                 other_info_handlers: Dict[str, Callable[[
                     Text], Union[str, list]]] = dict(),
                 unit_post_handler: BasePostHandler = do_nothing,
                 resource_field: str = None,
                 ud_post_handler: Callable[[Dict, Dict], None] = None
                 ):
        """
        :param project_path: 项目根路径
        :param result_dict: 存储结果的字典
        :param target_type: target类型，eg："shared_library"
        :param match_pattern: 用于进行的模式，eg：r"^( *)shared_library\(.*?\)"
        :param sub_com_dict: 从get_subsystem_component.py运行结果加载进来的dict，包含oh整体上的子系统、部件及其路径信息
        :param target_name_parser: 解析target名字的Callable
        :param other_info_handlers: 对其他信息进行收集处理，eg：{"sources": SourcesParser}——表示要处理target段落中的sources属性，
                           SourceParser是对target段落进行分析处理的Callable，接受一个字符串作为参数
        :param unit_post_handler: 对最终要存储的结果字典进行后处理，应当返回一个字符串作为存储时的key，且该key应为预期产物去除前后缀后的名字
        :resource_field: 针对资源类target,资源字段,如files = ["a.txt","b.txt"],则field为files
        :ud_post_handler: 参数为unit和result_dict的handler
        """
        if target_type not in result_dict.keys():
            result_dict[target_type] = dict()
        self.project_path = project_path
        self.result_dict = result_dict
        self.target_type = target_type
        self.match_pattern = match_pattern
        self.gn_file_line_no_dict = gn_lineno_collect(
            self.match_pattern, self.project_path)
        self.sc_dict = sub_com_dict
        self.target_name_parser = target_name_parser
        self.other_info_handlers = other_info_handlers
        self.unit_post_handler = unit_post_handler
        self.resource_field = resource_field
        self.ud_post_handler = ud_post_handler

    def _append(self, key: str, unit: Dict) -> None:
        """
        将target的结果存储到最终的结果字典中
        :param key：进行存储的key，应为预期的文件名
        :param unit: 要存储的target
        :return: None
        """
        self.result_dict.get(self.target_type)[key] = unit

    def _find_sc(self, gn_path: str):
        # gn_path与project_path都应当是绝对路径
        if not gn_path.startswith(self.project_path):
            logging.error("gn_path and project_path is not consistent: gn_path={}, project_path={}".format(
                gn_path, self.project_path))
            return str(), str()
        gp = gn_path.replace(self.project_path, "").lstrip(os.sep)
        alter_list = list()
        for k, v in self.sc_dict.items():
            if gp.startswith(k):
                alter_list.append(k)
        if not alter_list:
            return str(), str()
        alter_list.sort(key=lambda x: len(x), reverse=True)
        return self.sc_dict[alter_list[0]].get("subsystem"),  self.sc_dict[alter_list[0]].get("component")

    @abstractmethod
    def run(self):
        ...

    def __call__(self, *args, **kwargs):
        self.run()


def _gn_var_process(project_path: str, gn_v: str, alt_v: str, gn_path: str, ifrom: str, efrom: str, strip_quote: bool = False) -> Tuple[str, str]:
    """
    :param project_path:项目根路径
    :gn_v:gn中的值(可能为变量或空)
    :alt_v: 如果gn_v为空,则直接使用alt_v代替
    :gn_path: gn文件的路径
    :ifrom: 如果gn_v不为空,则其来自哪个字段
    :efrom: 如果gn_v为空,则其(准确来说是alt_v)来自哪个字段
    """
    if strip_quote:
        gn_v = gn_v.strip('"')
    if gn_v:
        if GnCommonTool.contains_gn_variable(gn_v):
            gn_v = GnCommonTool.replace_gn_variables(
                gn_v, gn_path, project_path).strip('"')
        else:
            gn_v = gn_v.strip('"')
        gn_f = ifrom
    else:
        gn_v = alt_v
        gn_f = efrom
    return gn_v, gn_f


class DefaultProcessor(BaseProcessor):
    
    @property
    def UNDEFINED(self):
        return "UNDEFINED"

    def helper(self, target_name: str, paragraph: str, gn_path: str, line_no: int, _sub: str, _com: str) -> Tuple[str]:
        output_name = GnVariableParser.string_parser("output_name", paragraph)
        output_name, out_from = _gn_var_process(self.project_path,
                                                output_name, target_name, gn_path, "target_name", "target_name", True)
        sub = GnVariableParser.string_parser("subsystem_name", paragraph)
        com = GnVariableParser.string_parser("part_name", paragraph)
        sub, sub_from = _gn_var_process(
            self.project_path, sub, _sub, gn_path, "gn", "json", True)
        com, com_from = _gn_var_process(
            self.project_path, com, _com, gn_path, "gn", "json", True)
        if not sub:
            sub = self.UNDEFINED
        if not com:
            com = self.UNDEFINED
        result = {
            "gn_path": gn_path,
            "target_type": self.target_type,
            "line_no": line_no,
            "subsystem_name": sub,
            "component_name": com,
            "subsystem_from": sub_from,
            "component_from": com_from,
            "target_name": target_name,
            "output_name": output_name,
            "output_from": out_from,
        }
        for k, h in self.other_info_handlers.items():
            result[k] = h(paragraph)
        key = self.unit_post_handler(result)
        self._append(key, result)
        if self.ud_post_handler:
            self.ud_post_handler(result, self.result_dict)

    def run(self):
        for gn_path, line_no_list in self.gn_file_line_no_dict.items():
            # 该路径下的主要的subsystem_name与component_name，如果target中没有指定，则取此值，如果指定了，则以target中的为准
            _sub, _com = self._find_sc(gn_path)
            with open(gn_path, 'r', encoding='utf-8') as f:
                content = f.read()
                itr = BasicTool.match_paragraph(
                    content, start_pattern=self.target_type)
                for line_no, p in zip(line_no_list, itr):
                    paragraph = p.group()
                    target_name = self.target_name_parser(paragraph).strip('"')
                    if not target_name:
                        continue
                    if GnCommonTool.contains_gn_variable(target_name, quote_processed=True):
                        possible_name_list = GnCommonTool.find_values_of_variable(target_name, path=gn_path,
                                                                                  stop_tail=self.project_path)
                        for n in possible_name_list:
                            self.helper(n, paragraph, gn_path,
                                        line_no, _sub, _com)
                    else:
                        self.helper(target_name, paragraph,
                                    gn_path, line_no, _sub, _com)


class StrResourceProcessor(DefaultProcessor):
    def helper(self, target_name: str, paragraph: str, gn_path: str, line_no: int, _sub: str, _com: str) -> Tuple[str]:
        resources = GnVariableParser.string_parser(
            self.resource_field, paragraph)
        if not resources:
            return
        _, resources = os.path.split(resources.strip('"'))

        if GnCommonTool.contains_gn_variable(resources):
            resources = GnCommonTool.replace_gn_variables(
                resources, gn_path, self.project_path).strip('"')
        sub = GnVariableParser.string_parser("subsystem_name", paragraph)
        com = GnVariableParser.string_parser("part_name", paragraph)
        sub, sub_from = _gn_var_process(
            self.project_path, sub, _sub, gn_path, "gn", "json")
        com, com_from = _gn_var_process(
            self.project_path, com, _com, gn_path, "gn", "json")
        if not sub:
            sub = self.UNDEFINED
        if not com:
            com = self.UNDEFINED
        _, file_name = os.path.split(resources)
        result = {
            "gn_path": gn_path,
            "target_type": self.target_type,
            "line_no": line_no,
            "subsystem_name": sub,
            "component_name": com,
            "subsystem_from": sub_from,
            "component_from": com_from,
            "target_name": target_name,
            "output_name": file_name,
            "output_from": "file_name",
        }
        for k, h in self.other_info_handlers.items():
            result[k] = h(paragraph)
        key = self.unit_post_handler(result)
        self._append(key, result)


class ListResourceProcessor(DefaultProcessor):

    def helper(self, target_name: str, paragraph: str, gn_path: str, line_no: int, _sub: str, _com: str) -> Tuple[str]:
        resources = GnVariableParser.list_parser(
            self.resource_field, paragraph)
        if not resources:
            return
        sub = GnVariableParser.string_parser("subsystem_name", paragraph)
        com = GnVariableParser.string_parser("part_name", paragraph)
        sub, sub_from = _gn_var_process(
            self.project_path, sub, _sub, gn_path, "gn", "json")
        com, com_from = _gn_var_process(
            self.project_path, com, _com, gn_path, "gn", "json")
        if not sub:
            sub = self.UNDEFINED
        if not com:
            com = self.UNDEFINED
        for ff in resources:
            _, file_name = os.path.split(ff)
            result = {
                "gn_path": gn_path,
                "target_type": self.target_type,
                "line_no": line_no,
                "subsystem_name": sub,
                "component_name": com,
                "subsystem_from": sub_from,
                "component_from": com_from,
                "target_name": target_name,
                "output_name": file_name,
                "output_from": "file_name",
            }
            for k, h in self.other_info_handlers.items():
                result[k] = h(paragraph)
            key = self.unit_post_handler(result)
            self._append(key, result)


if __name__ == '__main__':
    ...
