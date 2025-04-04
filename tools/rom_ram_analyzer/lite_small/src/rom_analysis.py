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

# This file is for rom analyzation of lite/small devices.

"""
1. 先收集BUILD.gn中的target信息
2. 然后根据编译产物到1中进行搜索,匹配其所属的部件

对于ohos开头的template,主要根据其component字段和subsystem_name字段来归数其部件；同时也要考虑install_dir字段
对于gn原生的template,主要根据bundle.json中的字段来归属其部件

对于找不到的,可以模糊匹配,如,有产物libxxx,则可以在所有的BUILD.gn中搜索xxx,并设置一个阀值予以过滤
"""

import sys
import argparse
import json
import logging
import os
from typing import Dict, List, Tuple, Text
import copy
import preprocess
from time import time
from concurrent.futures import ThreadPoolExecutor, Future
from threading import RLock
import collections

from config import result_dict, collector_config, configs, \
    project_path, sub_com_dict, product_name, recollect_gn, baseline, unit_adapt, output_file
from pkgs.basic_tool import BasicTool, unit_adaptive
from pkgs.gn_common_tool import GnCommonTool
from pkgs.simple_excel_writer import SimpleExcelWriter
from pkgs.rom_ram_baseline_collector import RomRamBaselineCollector
from misc import gn_lineno_collect


class RomAnalysisTool:
    @classmethod
    def analysis(cls, product_info: str, product_dict: Dict[str, List[str]], output_file_name: str):
        """analysis the rom of lite/small product

        Args:
            product_info (str): product name configured in the yaml
            product_dict (Dict[str, List[str]]): result dict of compiled product file
                format:
                    "bin":[...],
                    "so":[...]
                    ...
        """
        logging.info("start analyzing...")
        rom_ram_baseline: Dict[str, Dict] = RomRamBaselineCollector.collect(
            project_path)
        with os.fdopen(os.open("rom_ram_baseline.json", os.O_WRONLY | os.O_CREAT, mode=0o640), 'w',
                       encoding='utf-8') as f:
            json.dump(rom_ram_baseline, f, indent=4)
        gn_info_file = configs["gn_info_file"]  # filename to save gn_info
        with open(gn_info_file, 'r', encoding='utf-8') as f:
            gn_info = json.load(f)
        query_order: Dict[str, List[str]
                          ] = configs[product_info]["query_order"]  # query order of the gn template to be matched
        query_order["etc"] = configs["target_type"]  # etc会查找所有的template
        rom_size_dict: Dict = dict()
        if "manual_config" in configs[product_info].keys():
            cls._match_manual_configured(
                configs[product_info]["manual_config"], product_dict, configs[product_info]["product_dir"]["root"],
                rom_size_dict)
        cls._subsystem_component_for_all_product_file(
            product_dict, query_order, gn_info, gn_info_file, rom_ram_baseline, rom_size_dict)
        if unit_adapt:
            cls._result_unit_adaptive(rom_size_dict)
        with os.fdopen(os.open(output_file_name + ".json", os.O_WRONLY | os.O_CREAT, mode=0o640), 'w',
                       encoding='utf-8') as f:
            json.dump(rom_size_dict, f, indent=4)
        cls._save_as_xls(rom_size_dict, product_info, baseline)
        logging.info("success")

    @classmethod
    def collect_gn_info(cls):
        logging.info("start scanning BUILD.gn")
        with ThreadPoolExecutor(max_workers=len(collector_config) + 1) as pool:
            future_list: List[Future] = list()
            for c in collector_config:
                future_list.append(pool.submit(c))
            for f in future_list:
                f.result()
        gn_info_file = configs["gn_info_file"]
        with os.fdopen(os.open(gn_info_file, os.O_WRONLY | os.O_CREAT, mode=0o640), 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=4)
    
    @classmethod
    def collect_product_info(cls, product_name: str):
        logging.info("start scanning compile products")
        product_dict: Dict[str, List[str]] = cls._find_files(product_name)
        with os.fdopen(os.open(configs[product_name]["product_infofile"], os.O_WRONLY | os.O_CREAT, mode=0o640), 'w', encoding='utf-8') as f:
            json.dump(product_dict, f, indent=4)
        return product_dict

    @classmethod
    def _add_rest_dir(cls, top_dir: str, rela_path: str, sub_path: str, dir_list: List[str]) -> None:
        """
        :top_dir 顶层目录,不会变化
        :rela_path 最顶层的值为空
        :sub_path 一般是a/b/c这种形式
        :dir_list 相对于原始top目录的子目录的全路径
        example: 
        /
        |-a
        |-b
        |-c
        |-|-d
        |-|-e
        |-|-f
        |-|-|-g
        |-|-|-h
        top_dir: /
        rela_path: ""
        sub_path: c/e
        dir_list: [c]
        => [c/d, c/f], assume 'a' and 'b' has been removed from dir_list
        """
        if (not sub_path) or (os.sep not in sub_path):
            return
        # 将其他目录添加到dir_list
        t, sub_sub_path = sub_path.split(os.sep, 1)  # 如果是c/e,分割成c,e
        t = os.path.join(rela_path, t)
        if t in dir_list:
            dir_list.remove(t)
        sub_sub_dir_list = os.listdir(os.path.join(top_dir, t))
        for ssdl in sub_sub_dir_list:
            if os.path.join(rela_path, sub_path) != os.path.join(t, ssdl):
                dir_list.append(os.path.join(t, ssdl))
        if not sub_sub_dir_list:
            return
        cls._add_rest_dir(top_dir, t, sub_sub_path, dir_list)

    @classmethod
    def _find_files(cls, product_name: str) -> Dict[str, List[str]]:
        product_dir: Dict[str, Dict] = configs[product_name]["product_dir"]
        if not product_name:
            logging.error(
                f"product_name '{product_name}' not found in the config.yaml")
            exit(1)
        product_path_dit: Dict[str, str] = dict()  # 存储编译产物的类型及目录
        root_dir = product_dir.get("root")
        root_dir = os.path.join(project_path, root_dir)
        relative_dir: Dict[str, str] = product_dir.get("relative")
        if not relative_dir:
            logging.warning(
                f"'relative_dir' of {product_name} not found in the config.yaml")
            exit(1)
        # 除了so a hap bin外的全部归到etc里面
        for k, v in relative_dir.items():
            product_path_dit[k] = os.path.join(root_dir, v)
        # 查找编译产物信息
        # product_dict格式: {"so": ["a.so", "b.so"]}
        product_dict: Dict[str, List[str]] = dict()  # 存储编译产物的名称
        for k, v in product_path_dit.items():
            if not os.path.exists(v):
                logging.warning(f"dir '{v}' not exist")
            product_dict[k] = BasicTool.find_files_with_pattern(v)  # v是全路径
        if product_dir.get("rest"):
            rest_dir_list: List[str] = os.listdir(
                root_dir)  # 除了配置在relative下之外的所有剩余目录,全部归到etc下
            for v in relative_dir.values():
                if v in rest_dir_list:
                    rest_dir_list.remove(v)
            for v in relative_dir.values():
                if os.sep in v:
                    cls._add_rest_dir(root_dir, str(), v, rest_dir_list)
            if "etc" not in product_dict.keys():
                product_dict["etc"] = list()
            for r in rest_dir_list:
                product_dict["etc"].extend(
                    BasicTool.find_files_with_pattern(os.path.join(root_dir, r)))
        return product_dict

    @classmethod
    def _put(cls, sub: str, com: str, unit: Dict, rom_size_dict: Dict, com_size_baseline: str = str()):
        size = unit.get("size")
        if not rom_size_dict.get("size"):  # 总大小
            rom_size_dict["size"] = 0
        if not rom_size_dict.get(sub):  # 子系统大小
            rom_size_dict[sub]: Dict[str, Dict] = dict()
            rom_size_dict[sub]["size"] = 0
            rom_size_dict[sub]["count"] = 0

        if not rom_size_dict.get(sub).get(com):  # 部件
            rom_size_dict.get(sub)[com] = dict()
            rom_size_dict[sub][com]["filelist"] = list()
            rom_size_dict[sub][com]["size"] = 0
            rom_size_dict[sub][com]["count"] = 0

        if (sub != "NOTFOUND" and sub != "UNDEFINED" and com != "NOTFOUND" and com != "UNDEFINED") \
                and (not rom_size_dict.get(sub).get(com).get("baseline")) and baseline:
            rom_size_dict[sub][com]["baseline"] = com_size_baseline

        rom_size_dict[sub][com]["filelist"].append(unit)
        rom_size_dict[sub][com]["size"] += size
        rom_size_dict[sub][com]["count"] += 1
        rom_size_dict[sub]["size"] += size
        rom_size_dict[sub]["count"] += 1
        rom_size_dict["size"] += size

    @classmethod
    def _fuzzy_match(cls, file_name: str, filter_path_keyword: Tuple[str] = tuple()) -> Tuple[str, str, str]:
        """
        TODO 应当先遍历gn_info进行匹配
        直接grep,利用出现次数最多的BUILD.gn去定位subsystem_name和component_name"""
        logging.info(f"fuzzy match: {file_name}")
        _, base_name = os.path.split(file_name)
        if base_name.startswith("lib"):
            base_name = base_name[3:]
        if base_name.endswith(".a"):
            base_name = base_name[:base_name.index(".a")]
        elif base_name.endswith(".z.so"):
            base_name = base_name[:base_name.index(".z.so")]
        elif base_name.endswith(".so"):
            base_name = base_name[:base_name.index(".so")]
        exclude_dir = configs["black_list"]
        tbl = [x for x in exclude_dir if os.sep in x]

        def handler(content: Text) -> List[str]:
            t = list(filter(lambda y: len(y) > 0, list(
                map(lambda x: x.strip(), content.split("\n")))))
            for item in tbl:
                p = os.path.join(project_path, item)
                t = list(filter(lambda x: p not in x, t))
            return t

        grep_result: List[str] = BasicTool.grep_ern(
            base_name,
            project_path,
            include="BUILD.gn",
            exclude=tuple(exclude_dir),
            post_handler=handler)
        if filter_path_keyword:
            tmp = list()
            for gr in grep_result:
                for item in filter_path_keyword:
                    if item in gr:
                        continue
                    tmp.append(gr)
            grep_result = tmp
        if not grep_result:
            logging.info(f"fuzzy match failed.")
            return str(), str(), str()
        gn_dict: Dict[str, int] = collections.defaultdict(int)
        for g in grep_result:
            gn = g.split(':')[0].replace(project_path, "").lstrip(os.sep)
            gn_dict[gn] += 1
        gn_file, _ = collections.Counter(gn_dict).most_common(1)[0]
        for k, v in sub_com_dict.items():
            if gn_file.startswith(k):
                s = v.get("subsystem")
                c = v.get("component")
                logging.info(
                    f"fuzzy match success: subsystem_name={s}, component_name={c}")
                return gn_file, s, c
        logging.info(f"fuzzy match failed.")
        return str(), str(), str()

    @classmethod
    def _get_one_line(cls, baseline_info, subsystem_name, component_name, component_baseline, file_name, file_size):
        if baseline_info:
            return [subsystem_name, component_name,
                    component_baseline, file_name, file_size]
        else:
            return [subsystem_name, component_name,
                    file_name, file_size]

    @classmethod
    def _save_as_xls(cls, result_dict_info: Dict, product_name_info: str, baseline_info: bool) -> None:
        logging.info("saving as xls...")
        header = ["subsystem_name", "component_name", "output_file", "size(Byte)"]
        if baseline_info:
            header = ["subsystem_name", "component_name", "baseline", "output_file", "size(Byte)"]
        tmp_dict = dict()
        for key in result_dict_info.keys():
            tmp_dict[key] = result_dict_info[key]
        excel_writer = SimpleExcelWriter("rom")
        excel_writer.set_sheet_header(headers=header)
        (subsystem_start_row, subsystem_end_row, subsystem_col, component_start_row, component_end_row,
         component_col, baseline_col) = (1, 0, 0, 1, 0, 1, 2)
        if "size" in tmp_dict.keys():
            del tmp_dict["size"]
        for subsystem_name in tmp_dict.keys():
            subsystem_dict = tmp_dict.get(subsystem_name)
            subsystem_size = subsystem_dict.get("size")
            subsystem_file_count = subsystem_dict.get("count")
            del subsystem_dict["count"]
            del subsystem_dict["size"]
            subsystem_end_row += subsystem_file_count

            for component_name in subsystem_dict.keys():
                component_dict: Dict[str, int] = subsystem_dict.get(
                    component_name)
                component_size = component_dict.get("size")
                component_file_count = component_dict.get("count")
                component_baseline = component_dict.get("baseline")
                if component_baseline:
                    del component_dict["baseline"]
                del component_dict["count"]
                del component_dict["size"]
                component_end_row += component_file_count

                for fileinfo in component_dict.get("filelist"):
                    file_name = fileinfo.get("file_name")
                    file_size = fileinfo.get("size")
                    line = cls._get_one_line(baseline_info, subsystem_name, component_name, component_baseline,
                                             file_name, file_size)
                    excel_writer.append_line(line)
                excel_writer.write_merge(component_start_row, component_col, component_end_row, component_col,
                                         component_name)
                if baseline_info:
                    excel_writer.write_merge(component_start_row, baseline_col, component_end_row, baseline_col,
                                             component_baseline)
                component_start_row = component_end_row + 1
            excel_writer.write_merge(subsystem_start_row, subsystem_col, subsystem_end_row, subsystem_col,
                                     subsystem_name)
            subsystem_start_row = subsystem_end_row + 1
        output_name: str = configs[product_name_info]["output_name"]
        output_name = output_name.replace(".json", ".xls")
        excel_writer.save(output_name)
        logging.info("save as xls success.")

    @classmethod
    def _result_unit_adaptive(cls, output_result_dict: Dict[str, Dict]) -> None:
        total_size = unit_adaptive(output_result_dict["size"])
        del output_result_dict["size"]
        for subsystem_name, subsystem_info in output_result_dict.items():
            sub_size = unit_adaptive(subsystem_info["size"])
            count = subsystem_info["count"]
            del subsystem_info["size"]
            del subsystem_info["count"]
            for component_name, component_info in subsystem_info.items():
                component_info["size"] = unit_adaptive(component_info["size"])
            subsystem_info["size"] = sub_size
            subsystem_info["count"] = count
        output_result_dict["size"] = total_size

    @classmethod
    def _match_manual_configured(cls, manual_config_info: Dict[str, Dict], compiled_files: Dict[str, List],
                                 compiled_root_path: str, output_result_dict: Dict[str, Dict]) -> None:
        for file_path, file_info in manual_config_info.items():
            full_path = os.path.join(
                project_path, compiled_root_path, file_path)
            if not os.path.isfile(full_path):
                logging.warning(f"config error: {file_path} is not a file.")
                continue
            file_info["size"] = os.path.getsize(full_path)
            file_info["file_name"] = full_path
            cls._put(file_info["subsystem"],
                     file_info["component"], file_info, output_result_dict)
            for _, v in compiled_files.items():
                if full_path not in v:
                    continue
                index = v.index(full_path)
                del v[index]
                break

    @classmethod
    def _iterate_all_template_type(cls, type_list: List[str], gn_info: Dict, gn_info_file: str, base_name: str,
                                   rom_ram_baseline: Dict, rom_size_dict: Dict, f: str, size: int):
        find_flag = False
        component_rom_baseline = None
        for tn in type_list:  # tn example: ohos_shared_library
            if find_flag:  # 如果已经在前面的template中找到了,后面的就不必再查找
                break
            output_dict: Dict[str, Dict] = gn_info.get(
                tn)  # 这个模板对应的所有可能编译产物
            if not output_dict:
                logging.warning(
                    f"'{tn}' not found in the {gn_info_file}")
                continue
            d = output_dict.get(base_name)
            if not d:
                continue
            d["size"] = size
            d["file_name"] = f.replace(project_path, "")
            if rom_ram_baseline.get(d["subsystem_name"]) and rom_ram_baseline.get(d["subsystem_name"]).get(
                    d["component_name"]):
                component_rom_baseline = rom_ram_baseline.get(
                    d["subsystem_name"]).get(d["component_name"]).get("rom")
            cls._put(d["subsystem_name"],
                     d["component_name"], d, rom_size_dict, component_rom_baseline)
            find_flag = True
        if not find_flag:  # 如果指定序列中的template都没有查找到,则模糊匹配
            # fuzzy match
            psesudo_gn, sub, com = cls._fuzzy_match(f)
            if sub and com:
                if rom_ram_baseline.get(sub) and rom_ram_baseline.get(sub).get(com):
                    component_rom_baseline = rom_ram_baseline.get(
                        sub).get(com).get("baseline")
                cls._put(sub, com, {
                    "subsystem_name": sub,
                    "component_name": com,
                    "psesudo_gn_path": psesudo_gn,
                    "description": "fuzzy match",
                    "file_name": f.replace(project_path, ""),
                    "size": size,
                }, rom_size_dict, component_rom_baseline)
                find_flag = True
        if not find_flag:  # 模糊匹配都没有匹配到的,归属到NOTFOUND
            cls._put("NOTFOUND", "NOTFOUND", {
                "file_name": f.replace(project_path, ""),
                "size": size,
            }, rom_size_dict)

    @classmethod
    def _subsystem_component_for_all_product_file(cls, product_dict: Dict[str, List[str]],
                                                  query_order: Dict[str, List[str]],
                                                  gn_info: Dict, gn_info_file: str, rom_ram_baseline: Dict,
                                                  rom_size_dict: Dict):
        for t, l in product_dict.items():
            for f in l:  # 遍历所有文件
                if os.path.isdir(f):
                    continue
                type_list = query_order.get(t)
                _, base_name = os.path.split(f)
                size = os.path.getsize(f)
                if not type_list:
                    logging.warning(
                        f"'{t}' not found in query_order of the config.yaml")
                    break
                cls._iterate_all_template_type(
                    type_list, gn_info, gn_info_file, base_name, rom_ram_baseline, rom_size_dict, f, size)


def main():
    if recollect_gn:
        RomAnalysisTool.collect_gn_info()
    product_dict: Dict[str, List[str]
    ] = RomAnalysisTool.collect_product_info(product_name)
    RomAnalysisTool.analysis(product_name, product_dict, output_file)


if __name__ == "__main__":
    main()
