#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

# This file provide the detection tool for unconditional dependence of required components on optional components.

import argparse
import json
import os
import re


class Analyzer:
    @classmethod
    def __get_open_components(cls, xml_path):
        open_components = list()
        with open(xml_path, 'r', encoding='utf-8') as r:
            xml_info = r.readlines()
        for line in xml_info:
            if "path=" in line:
                tmp = re.findall('path="(.*?)"', line)[0]
                open_components.append(tmp.split('/')[-1])
        return open_components

    @classmethod
    def __deal_config_json(cls, config_json):
        components = list()
        for subsystem in config_json['subsystems']:
            for component in subsystem['components']:
                if component not in components:
                    components.append(component['component'])
        return components

    @classmethod
    def __get_required_components(cls, config_path: str):
        required_components = list()
        files = os.listdir(config_path)
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(config_path, file), 'r', encoding='utf-8') as r:
                    config_json = json.load(r)
                required_components += cls.__deal_config_json(config_json)
        return required_components

    @classmethod
    def __get_line(cls, txt_list, key_words: str):
        for i in range(len(txt_list)):
            if key_words in txt_list[i]:
                return i + 1
        return 0

    @classmethod
    def __judge_deps(cls, gn_path: str, open_components_list, optional_components):
        error = list()
        deps = list()
        dependent_close = True
        with open(gn_path, 'r', encoding='utf-8') as r:
            gn = r.readlines()
        txt = ''
        for line in gn:
            txt += line
        key_txt = ' '.join(re.findall('if \(.+?\{(.*?)\}', txt))
        for component in open_components_list:
            if dependent_close == True:
                if component in txt:
                    dependent_close = False
        for i in range(len(gn)):
            dep_txt = re.findall('deps = \[(.*?)\]', gn[i]) + re.findall('deps += \[(.*?)\]', gn[i])
            dep_info = list()
            for info in dep_txt:
                if '/' in info:
                    dep_info += re.findall('/(.*?):', info)
                else:
                    dep_info += re.findall('"(.*?):', info)
            for component in optional_components:
                if component in dep_info and component not in key_txt:
                    deps.append((component, i + 1))
        if dependent_close == True and re.findall('deps =', txt):
            line = cls.__get_line(gn, 'deps =')
            error.append(
                {"line": line, "rule": "depend close component", "detail": "可能依赖闭源部件，请检查deps中的内容"})
        for one_dep in deps:
            error.append({"line": one_dep[1], "rule": "depend optional component",
                          "detail": "依赖开源部件中的非必选部件{}，请检查deps中的内容".format(one_dep[0])})
        return gn_path, error

    @classmethod
    def analysis(cls, gn_path_list, gn_component, config_path: str, open_components_path, result_json_name: str):
        if not os.path.exists(config_path):
            print("error: {} is inaccessible or not found".format(config_path))
            return
        if not os.path.exists(open_components_path):
            print("error: {} is inaccessible or not found".format(open_components_path))
            return
        if len(gn_path_list) != len(gn_component):
            print(
                "error: The component corresponding to the gn file and the gn file path are not in one-to-one correspondence.")
            return
        required_components = cls.__get_required_components(config_path)
        open_components = cls.__get_open_components(open_components_path)
        optional_components = list()
        for components in open_components:
            if components not in required_components:
                optional_components.append(components)
        result = list()
        for i in range(len(gn_path_list)):
            one_result = dict()
            if gn_component[i] in required_components:
                one_result["file_path"], one_result["error"] = cls.__judge_deps(gn_path_list[i], open_components,
                                                                                optional_components)
            else:
                one_result["file_path"], one_result["error"] = gn_path_list[i], []
            result.append(one_result)
        with os.fdopen(os.open(result_json_name + ".json", os.O_WRONLY | os.O_CREAT, mode=0o640), "w",
                       encoding='utf-8') as fd:
            json.dump(result, fd, indent=4, ensure_ascii=False)


def get_args():
    parser = argparse.ArgumentParser(
        description=f"analyze components deps.\n")
    parser.add_argument("-p", "--components_gn_path_list", required=True, type=str,
                        help="path of pr BUILD.gn")
    parser.add_argument("-g", "--gn_component", required=True, type=str,
                        help="gn file corresponding component")
    parser.add_argument("-c", "--config_path", required=True, type=str,
                        help="path of config_file")
    parser.add_argument("-o", "--open_component_xml_path", required=True, type=str,
                        help="open component name set")
    parser.add_argument("-r", "--result_json_name", type=str, default="result",
                        help="name of output_json")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    gn_path_list = args.components_gn_path_list.split(',')
    gn_component = args.gn_component.split(',')
    config_path = args.config_path
    open_components_xml_path = args.open_component_xml_path
    result_json_name = args.result_json_name
    Analyzer.analysis(gn_path_list, gn_component, config_path, open_components_xml_path, result_json_name)