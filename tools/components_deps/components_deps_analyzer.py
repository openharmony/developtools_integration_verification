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

# This file contains the comparison between mandatory components and the actual compiled components.

import argparse
import json
import os
import re


class Analyzer:
    @classmethod
    def __get_components(cls, config: str):
        mandatory_components = list()
        optional_components = list()
        with open(config, 'r', encoding='utf-8') as r:
            config_json = json.load(r)
        inherit = config_json['inherit']
        for json_name in inherit:
            with open(json_name, 'r', encoding='utf-8') as r:
                inherit_file = json.load(r)
            for subsystem in inherit_file['subsystems']:
                for component in subsystem['components']:
                    mandatory_components.append(component['component'])
        for subsystem in config_json['subsystems']:
            for component in subsystem['components']:
                if component not in mandatory_components:
                    optional_components.append(component['component'])
        return mandatory_components, optional_components

    @classmethod
    def __get_gn_path(cls, parts_deps: str, mandatory: list):
        mandatory_gn_path = dict()
        with open(parts_deps, 'r', encoding='utf-8') as r:
            parts_deps_json = json.load(r)
        for component in parts_deps_json:
            if component in mandatory and parts_deps_json[component]:
                mandatory_gn_path[component] = '/'.join(
                    parts_deps_json[component]['build_config_file'].split('/')[:-1])
        return mandatory_gn_path

    @classmethod
    def __judge_deps(cls, gn_path: str, optional_components):
        deps = list()
        with open(gn_path, 'r', encoding='utf-8') as r:
            gn = r.readlines()
        txt = ''
        for line in gn:
            txt += line.strip()
        for optional_component in optional_components:
            dep_txt = re.findall('deps = \[(.*?)\]', txt) + re.findall('deps += \[(.*?)\]', txt)
            dep_info = list()
            for info in dep_txt:
                if '/' in info:
                    dep_info += re.findall('/(.*?):', info)
                else:
                    dep_info += re.findall('"(.*?):', info)
            if optional_component in dep_info:
                key_txt = ' '.join(re.findall('if \(.+?\{(.*?)\}', txt))
                if optional_component not in key_txt:
                    deps.append({'component': optional_component, 'gn_path': gn_path})
        return deps

    @classmethod
    def __get_deps(cls, mandatory_gn: dict, optional_components_list: list):
        all_deps = dict()
        for component in mandatory_gn.keys():
            component_deps = list()
            total_deps = dict()
            for root, _, files in os.walk(mandatory_gn[component]):
                if 'BUILD.gn' in files:
                    component_deps += cls.__judge_deps(os.path.join(root, 'BUILD.gn'), optional_components_list)
            for one_dep in component_deps:
                if one_dep['component'] not in total_deps.keys():
                    total_deps[one_dep['component']] = [one_dep['gn_path']]
                else:
                    total_deps[one_dep['component']].append(one_dep['gn_path'])
            all_deps[component] = total_deps
        return all_deps

    @classmethod
    def analysis(cls, config_path: str, parts_deps_path: str, output_file: str):
        if not os.path.exists(config_path):
            print("error: {} is inaccessible or not found".format(config_path))
            return
        if not os.path.exists(parts_deps_path):
            print("error: {} is inaccessible or not found".format(parts_deps_path))
            return
        mandatory_components, optional_components = cls.__get_components(config_path)
        mandatory_components_gn_path = cls.__get_gn_path(parts_deps_path, mandatory_components)
        deps = cls.__get_deps(mandatory_components_gn_path, optional_components)
        with open(output_file + ".json", 'w', encoding='utf-8') as w:
            json.dump(deps, w, indent=4)


def get_args():
    parser = argparse.ArgumentParser(
        description=f"analyze components deps.\n")
    parser.add_argument("-c", "--config_json", required=True, type=str,
                        help="path of root path of openharmony/vendor/hihope/{product_name}/config.json")
    parser.add_argument("-d", "--parts_deps_json", required=True, type=str,
                        help="path of out/{product_name}/build_configs/parts_info/parts_deps.json")
    parser.add_argument("-o", "--output_file", type=str, default="components_deps",
                        help="eg: demo/components_deps")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = get_args()
    config_json_path = args.config_json
    parts_deps_json_path = args.parts_deps_json
    output_file_name = args.output_file
    Analyzer.analysis(config_json_path, parts_deps_json_path, output_file_name)