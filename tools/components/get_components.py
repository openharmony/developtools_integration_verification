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

# This file finds components of config.json.

import argparse
import json
import os


class Analyzer:
    @classmethod
    def get_components(cls, config: str, output_file: str):
        mandatory_components = list()
        optional_components = list()
        components = dict()
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
        components["components"] = mandatory_components + optional_components
        with os.fdopen(os.open(output_file + ".json", os.O_WRONLY | os.O_CREAT, mode=0o640), "w") as fd:
            json.dump(components, fd, indent=4)


def get_args():
    parser = argparse.ArgumentParser(
        description=f"analyze components deps.\n")
    parser.add_argument("-c", "--config_json", required=True, type=str,
                        help="path of root path of openharmony/vendor/hihope/{product_name}/config.json")
    parser.add_argument("-o", "--output_file", type=str, default="components",
                        help="eg: name of output_json_file")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    config_json_path = args.config_json
    output_file_name = args.output_file
    Analyzer.get_components(config_json_path, output_file_name)