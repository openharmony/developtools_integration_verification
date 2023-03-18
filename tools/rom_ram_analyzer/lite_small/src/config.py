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

# This file is a configuration for scaning the BUILD.gn to collection compile 
# products.


import os
import sys
import argparse
import json
import logging
from typing import *

import preprocess
from pkgs.simple_yaml_tool import SimpleYamlTool
from pkgs.basic_tool import do_nothing, BasicTool
from get_subsystem_component import SC
from misc import *
from template_processor import *
"""
只给rom_analysis.py使用
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="analysis rom size of L0 and L1 product")
    parser.add_argument("-p", "--product_name", type=str,
                        help="product name. eg: -p ipcamera_hispark_taurus")
    parser.add_argument("-o", "--oh_path", type=str,
                        default=".", help="root path of openharmony")
    parser.add_argument("-g", "--recollect_gn",
                        action="store_false", help="recollect gn info or not")
    parser.add_argument("-s", "--recollect_sc", action="store_false",
                        help="recollect subsystem_component info or not")
    args = parser.parse_args()
    return args


logging.basicConfig(level=logging.INFO)
_args = parse_args()

# # global variables
configs = SimpleYamlTool.read_yaml("config.yaml")
result_dict: Dict[str, Any] = dict()

project_path = BasicTool.abspath(_args.oh_path)
product_name = _args.product_name
recollect_gn = _args.recollect_gn
_recollect_sc = _args.recollect_sc
_sc_json: Dict[Text, Text] = configs.get("subsystem_component")
_sc_save = _sc_json.get("save")
_target_type = configs["target_type"]
_sc_output_path = _sc_json.get("filename")
if _recollect_sc:
    logging.info(
        "satrt scanning subsystem_name and component via get_subsystem_comonent.py")
    sub_com_dict: Dict = SC.run(project_path, _sc_output_path, _sc_save)
else:
    with open(_sc_output_path, 'r', encoding='utf-8') as f:
        sub_com_dict = json.load(f)

collector_config: Tuple[BaseProcessor] = (
    DefaultProcessor(project_path=project_path,    # 项目根路径
                     result_dict=result_dict,   # 保存结果的字典
                     # targte的类型名称,即xxx("yyy")中的xxx
                     target_type=_target_type[0],
                     # 用以进行匹配的模式串,包括匹配段落时作为前缀
                     match_pattern=fr"^( *){_target_type[0]}\(.*?\)",
                     sub_com_dict=sub_com_dict,    # 从bundle.json中收集的subsystem_name和component_name信息
                     target_name_parser=TargetNameParser.single_parser,  # 进行target_name解析的parser
                     other_info_handlers={
                         "extension": extension_handler,
                     },    # 解析其他信息的parser,{"字段名":该字段的parser}
                     unit_post_handler=SOPostHandler()  # 对即将进行存储的unit字典的handler,会返回一个str作为存储时的key
                     ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[1],
                     match_pattern=fr"^( *){_target_type[1]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "extension": extension_handler,
                     },
                     unit_post_handler=SOPostHandler(),
                     ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[2],
                     match_pattern=fr"^( *){_target_type[2]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "extension": extension_handler,
                     },
                     unit_post_handler=APostHandler(),
                     ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[3],
                     match_pattern=fr"^( *){_target_type[3]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "extension": extension_handler,
                     },
                     unit_post_handler=APostHandler(),
                     ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[4],
                     match_pattern=fr"^( *){_target_type[4]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "extension": extension_handler,
                     },
                     unit_post_handler=DefaultPostHandler(),
                     ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[5],
                     match_pattern=fr"^( *){_target_type[5]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "extension": extension_handler,
                     },
                     unit_post_handler=DefaultPostHandler(),
                     ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[6],
                     match_pattern=fr"^( *){_target_type[6]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "real_target_type": target_type_handler,
                         "extension": extension_handler,
                     },
                     unit_post_handler=LiteLibPostHandler(),
                     ud_post_handler=LiteLibS2MPostHandler,
                     ),
    DefaultProcessor(project_path=project_path,    # hap有个hap_name
                     result_dict=result_dict,
                     target_type=_target_type[7],
                     match_pattern=fr"^( *){_target_type[7]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "hap_name": hap_name_handler,
                         "extension": extension_handler,
                     },
                     unit_post_handler=HAPPostHandler(),
                     ),
    StrResourceProcessor(project_path=project_path,
                         result_dict=result_dict,
                         target_type=_target_type[8],
                         match_pattern=fr"^( *){_target_type[8]}\(.*?\)",
                         sub_com_dict=sub_com_dict,
                         target_name_parser=TargetNameParser.single_parser,
                         other_info_handlers={
                             "extension": extension_handler,
                         },
                         unit_post_handler=DefaultPostHandler(),
                         resource_field="source"
                         ),
    StrResourceProcessor(project_path=project_path,
                         result_dict=result_dict,
                         target_type=_target_type[9],
                         match_pattern=fr"^( *){_target_type[9]}\(.*?\)",
                         sub_com_dict=sub_com_dict,
                         target_name_parser=TargetNameParser.single_parser,
                         other_info_handlers={
                             "extension": extension_handler,
                         },
                         unit_post_handler=DefaultPostHandler(),
                         resource_field="source"
                         ),
    ListResourceProcessor(project_path=project_path,
                          result_dict=result_dict,
                          target_type=_target_type[10],
                          match_pattern=fr"^( *){_target_type[10]}\(.*?\)",
                          sub_com_dict=sub_com_dict,
                          target_name_parser=TargetNameParser.single_parser,
                          other_info_handlers={
                              "extension": extension_handler,
                          },
                          unit_post_handler=DefaultPostHandler(),
                          resource_field="sources"
                          ),
    StrResourceProcessor(project_path=project_path,
                         result_dict=result_dict,
                         target_type=_target_type[11],
                         match_pattern=fr"^( *){_target_type[11]}\(.*?\)",
                         sub_com_dict=sub_com_dict,
                         target_name_parser=TargetNameParser.single_parser,
                         other_info_handlers={
                             #  "extension": extension_handler,
                         },
                         unit_post_handler=DefaultPostHandler(),
                         resource_field="source"
                         ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[12],
                     match_pattern=fr"^( *){_target_type[12]}\(.*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.single_parser,
                     other_info_handlers={
                         "real_target_type": target_type_handler,
                         #  "extension": extension_handler,
                     },
                     unit_post_handler=LiteComponentPostHandler(),
                     ),
    DefaultProcessor(project_path=project_path,
                     result_dict=result_dict,
                     target_type=_target_type[13],
                     match_pattern=fr"^( *){_target_type[13]}\(.*?\, .*?\)",
                     sub_com_dict=sub_com_dict,
                     target_name_parser=TargetNameParser.second_parser,
                     other_info_handlers={
                     },
                     unit_post_handler=DefaultPostHandler(),
                     ud_post_handler=TargetS2MPostHandler
                     )
)

__all__ = ["configs", "result_dict", "collector_config", "sub_com_dict"]

if __name__ == '__main__':
    for c in collector_config:
        c.run()
    with open("demo.json", 'w', encoding='utf-8') as f:
        json.dump(result_dict, f)
