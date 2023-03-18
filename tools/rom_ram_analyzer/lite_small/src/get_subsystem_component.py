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

import argparse
import os
import json
import logging

g_subsystem_path_error = list()  # subsystem path exist in subsystem_config.json
# bundle.json path which cant get component path.
g_component_path_empty = list()
g_component_abs_path = list()  # destPath can't be absolute path.


def get_subsystem_components(ohos_path: str):
    subsystem_json_path = os.path.join(
        ohos_path, r"build/subsystem_config.json")
    subsystem_item = {}

    with open(subsystem_json_path, 'rb') as f:
        subsystem_json = json.load(f)
    # get sunsystems
    for i in subsystem_json:
        subsystem_name = subsystem_json[i]["name"]
        subsystem_path = os.path.join(ohos_path, subsystem_json[i]["path"])
        if not os.path.exists(subsystem_path):
            g_subsystem_path_error.append(subsystem_path)
            continue
        cmd = 'find {} -name bundle.json'.format(subsystem_path)
        bundle_json_list = os.popen(cmd).readlines()
        # get components
        component_list = []
        for j in bundle_json_list:
            bundle_path = j.strip()
            with open(bundle_path, 'rb') as bundle_file:
                bundle_json = json.load(bundle_file)
            component_item = {}
            if 'segment' in bundle_json and 'destPath' in bundle_json["segment"]:
                destpath = bundle_json["segment"]["destPath"]
                component_item[bundle_json["component"]["name"]] = destpath
                if os.path.isabs(destpath):
                    g_component_abs_path.append(destpath)
            else:
                component_item[bundle_json["component"]["name"]
                               ] = "Unknow. Please check {}".format(bundle_path)
                g_component_path_empty.append(bundle_path)
            component_list.append(component_item)
        subsystem_item[subsystem_name] = component_list
    return subsystem_item


def get_subsystem_components_modified(ohos_root) -> dict:
    ret = dict()
    subsystem_info = get_subsystem_components(ohos_root)
    if subsystem_info is None:
        return None
    for subsystem_k, subsystem_v in subsystem_info.items():
        for component in subsystem_v:
            for k, v in component.items():
                ret.update({v: {'subsystem': subsystem_k, 'component': k}})
    return ret


def export_to_json(subsystem_item: dict, output_filename: str):
    subsystem_item_json = json.dumps(
        subsystem_item, indent=4, separators=(', ', ': '))
    with open(output_filename, 'w') as f:
        f.write(subsystem_item_json)
    logging.info("output path: {}".format(output_filename))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="project root path.", type=str)
    parser.add_argument("-o", "--outpath",
                        help="specify an output path.", type=str)
    args = parser.parse_args()

    ohos_path = os.path.abspath(args.project)
    if not is_project(ohos_path):
        logging.error("'{}' is not a valid project path.".format(ohos_path))
        exit(1)

    output_path = r'.'
    if args.outpath:
        output_path = args.outpath

    return ohos_path, output_path


def is_project(path: str) -> bool:
    '''
    @func: 判断是否源码工程。
    @note: 通过是否含有 .repo/manifests 目录粗略判断。
    '''
    p = os.path.normpath(path)
    return os.path.exists('{}/.repo/manifests'.format(p))


def print_warning_info():
    '''@func: 打印一些异常信息。
    '''
    if g_component_path_empty or g_component_abs_path:
        logging.warning("------------ warning info ------------------")

    if g_component_path_empty:
        logging.warning("can't find destPath in:")
        logging.warning(g_component_path_empty)

    if g_component_abs_path:
        logging.warning("destPath can't be absolute path:")
        logging.warning(g_component_abs_path)


class SC:
    @classmethod
    def run(cls, project_path: str, output_path: str = None, save_result: bool = True):
        info = get_subsystem_components_modified(
            os.path.abspath(os.path.expanduser(project_path)))
        if save_result and output_path:
            export_to_json(info, output_path)
        print_warning_info()
        return info


__all__ = ["SC"]

if __name__ == '__main__':
    ohos_path, output_path = parse_args()
    # info = get_subsystem_components_modified(ohos_path)
    # export_to_json(info, output_path)
    # print_warning_info()
    SC.run(ohos_path, output_path)
