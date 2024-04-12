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

# This file is to collect baseline information (according to bundle.json)

from typing import Dict, Any
import json
import logging

if __name__ == '__main__':
    from basic_tool import BasicTool
else:
    from pkgs.basic_tool import BasicTool


class RomRamBaselineCollector:
    """collect baseline of rom and ram from bundle.json
    """

    @classmethod
    def collect(cls, oh_path: str) -> Dict[str, Dict]:
        def post_handler(x: str) -> list:
            x = x.split("\n")
            y = [item for item in x if item]
            return y

        bundle_list = BasicTool.execute(
            cmd=f"find {oh_path} -name bundle.json", post_processor=post_handler)
        rom_ram_baseline_dict: Dict[str, Dict] = dict()
        for bundle in bundle_list:
            with open(bundle, 'r', encoding='utf-8') as f:
                content: Dict[str, Any] = json.loads(f.read())
                component_info = content.get("component")
                if not component_info:
                    logging.warning(f"{bundle} has no field of 'component'.")
                    continue
                component_name = component_info.get("name")
                subsystem_name = component_info.get("subsystem")
                rom_baseline = component_info.get("rom")
                ram_baseline = component_info.get("ram")
                if not (subsystem_name or rom_baseline or ram_baseline):
                    logging.warning(
                        f"subsystem=\"{subsystem_name}\", rom=\"{rom_baseline}\", ram=\"{ram_baseline}\" in {bundle}")
                cls._put(rom_ram_baseline_dict, subsystem_name,
                         component_name, rom_baseline, ram_baseline, bundle)
        return rom_ram_baseline_dict
    
    @classmethod
    def _put(cls, result_dict: Dict, subsystem_name: str, component_name: str, rom_size: str, ram_size: str,
             bundle_path: str) -> None:
        if not result_dict.get(subsystem_name):
            result_dict[subsystem_name] = dict()
        result_dict[subsystem_name][component_name] = dict()
        result_dict[subsystem_name][component_name]["rom"] = rom_size
        result_dict[subsystem_name][component_name]["ram"] = ram_size
        result_dict[subsystem_name][component_name]["bundle.json"] = bundle_path