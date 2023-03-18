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

# This file contains a SimpleYamlTool, which is a implemented based on the package named yaml for easy use.

import yaml
from typing import *
from yaml.loader import SafeLoader


class SimpleYamlTool:
    @classmethod
    def read_yaml(cls, file_name: str, mode: str = "r", encoding: str = "utf-8") -> Dict:
        with open(file_name, mode, encoding=encoding) as f:
            return yaml.load(f, Loader=SafeLoader)


if __name__ == '__main__':
    config = SimpleYamlTool.read_yaml("/home/aodongbiao/build_static_check/tools/component_tools/rom_ram_analyzer/src/config.yaml")
    print(config["black_grep_dir"])