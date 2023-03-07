import sys
import argparse
import json
import logging
import os
from typing import *
import copy
import preprocess
from time import time
from concurrent.futures import ThreadPoolExecutor, Future
from threading import RLock
import collections

from config import result_dict, collector_config, configs, \
    project_path, sub_com_dict, product_name, recollect_gn
# from gn_info_collect import GnInfoCollector
from pkgs.basic_tool import BasicTool
from pkgs.gn_common_tool import GnCommonTool
from pkgs.simple_excel_writer import SimpleExcelWriter
from misc import gn_lineno_collect


"""
1. 先收集BUILD.gn中的target信息
2. 然后根据编译产物到1中进行搜索,匹配其所属的部件

对于ohos开头的template,主要根据其component字段和subsystem_name字段来归数其部件；同时也要考虑install_dir字段
对于gn原生的template,主要根据bundle.json中的字段来归属其部件

对于找不到的,可以模糊匹配,如,有产物libxxx,则可以在所有的BUILD.gn中搜索xxx,并设置一个阀值予以过滤
"""


class RomAnalysisTool:
    @classmethod
    def collect_gn_info(cls):
        with ThreadPoolExecutor(max_workers=len(collector_config) + 1) as pool:
            future_list: List[Future] = list()
            for c in collector_config:
                future_list.append(pool.submit(c))
            for f in future_list:
                f.result()
        gn_info_file = configs["gn_info_file"]
        with open(gn_info_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=4)

    @classmethod
    def _add_rest_dir(cls, top_dir: str, rela_path: str, sub_path: str, dir_list: List[str]) -> None:
        """
        dir_list:相对于原始top目录的所有子目录的全路径
        """
        if not sub_path:
            return
        # 将其他目录添加到dir_list
        all_subdir = os.listdir(os.path.join(top_dir, rela_path))
        for d in all_subdir:
            t = os.path.join(rela_path, d)
            if os.path.isdir(os.path.join(top_dir, t)) and t not in dir_list:
                dir_list.append(t)
        # 移除sub_path的当前层级的目录
        t = sub_path.split(os.sep)
        if os.path.join(rela_path, t[0]) in dir_list:
            dir_list.remove(os.path.join(rela_path, t[0]))
        else:
            logging.error(
                f"'{os.path.join(rela_path,t[0])}' not in '{top_dir}'")
        sp = str()
        if len(t) == 1:
            return
        elif len(t) == 2:
            sp = t[1]
        else:
            sp = os.path.join(*t[1:])
        cls._add_rest_dir(top_dir, os.path.join(rela_path, t[0]), sp, dir_list)

    @classmethod
    def _find_files(cls, product_name: str) -> Dict[str, List[str]]:
        product_dir: Dict[str, Dict] = configs[product_name]["product_dir"]
        if not product_name:
            logging.error(
                f"product_name '{product_name}' not found in the config.yaml")
            exit(1)
        product_path_dit: Dict[str, str] = dict()   # 存储编译产物的类型及目录
        root_dir = product_dir.get("root")
        root_dir = os.path.join(project_path, root_dir)
        relative_dir: Dict[str, str] = product_dir.get("relative")
        if not relative_dir:
            logging.warning(
                f"'{relative_dir}' of {product_name} not found in the config.yaml")
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
                cls._add_rest_dir(root_dir, str(), v, rest_dir_list)
            if "etc" not in product_dict.keys():
                product_dict["etc"] = list()
            for r in rest_dir_list:
                product_dict["etc"].extend(
                    BasicTool.find_files_with_pattern(os.path.join(root_dir, r)))
        return product_dict

    @classmethod
    def collect_product_info(cls, product_name: str):
        product_dict: Dict[str, List[str]] = cls._find_files(product_name)
        with open(configs[product_name]["product_infofile"], 'w', encoding='utf-8') as f:
            json.dump(product_dict, f, indent=4)
        return product_dict

    @classmethod
    def _put(cls, sub: str, com: str, unit: Dict, rom_size_dict: Dict):
        size = unit.get("size")
        if not rom_size_dict.get("size"):   # 总大小
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

        rom_size_dict[sub][com]["filelist"].append(unit)
        rom_size_dict[sub][com]["size"] += size
        rom_size_dict[sub][com]["count"] += 1
        rom_size_dict[sub]["size"] += size
        rom_size_dict[sub]["count"] += 1
        rom_size_dict["size"] += size

    @classmethod
    def _fuzzy_match(cls, file_name: str, extra_black_list: Tuple[str] = ("test",)) -> Tuple[str, str, str]:
        """
        直接grep,利用出现次数最多的BUILD.gn去定位subsystem_name和component_name"""
        _, base_name = os.path.split(file_name)
        if base_name.startswith("lib"):
            base_name = base_name[3:]
        if base_name.endswith(".a"):
            base_name = base_name[:base_name.index(".a")]
        elif base_name.endswith(".z.so"):
            base_name = base_name[:base_name.index(".z.so")]
        elif base_name.endswith(".so"):
            base_name = base_name[:base_name.index(".so")]
        exclude_dir = [os.path.join(project_path, x)
                       for x in configs["black_list"]]
        exclude_dir.extend(list(extra_black_list))
        grep_result: List[str] = BasicTool.grep_ern(
            base_name,
            project_path,
            include="BUILD.gn",
            exclude=tuple(exclude_dir),
            post_handler=lambda x: list(filter(lambda x: len(x) > 0, x.split('\n'))))
        if not grep_result:
            return str(), str(), str()
        gn_dict: Dict[str, int] = collections.defaultdict(int)
        for g in grep_result:
            gn = g.split(':')[0].replace(project_path, "").lstrip(os.sep)
            gn_dict[gn] += 1
        gn_file, _ = collections.Counter(gn_dict).most_common(1)[0]
        for k, v in sub_com_dict.items():
            if gn_file.startswith(k):
                return gn_file, v.get("subsystem"), v.get("component")
        return str(), str(), str()

    @classmethod
    def _save_as_xls(cls, result_dict: Dict, product_name: str) -> None:
        header = ["subsystem_name", "component_name",
                  "output_file", "size(Byte)"]
        tmp_dict = copy.deepcopy(result_dict)
        excel_writer = SimpleExcelWriter("rom")
        excel_writer.set_sheet_header(headers=header)
        subsystem_start_row = 1
        subsystem_end_row = 0
        subsystem_col = 0
        component_start_row = 1
        component_end_row = 0
        component_col = 1
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
                del component_dict["count"]
                del component_dict["size"]
                component_end_row += component_file_count

                for fileinfo in component_dict.get("filelist"):
                    file_name = fileinfo.get("file_name")
                    file_size = fileinfo.get("size")
                    excel_writer.append_line(
                        [subsystem_name, component_name, file_name, file_size])
                excel_writer.write_merge(component_start_row, component_col, component_end_row, component_col,
                                         component_name)
                component_start_row = component_end_row + 1
            excel_writer.write_merge(subsystem_start_row, subsystem_col, subsystem_end_row, subsystem_col,
                                     subsystem_name)
            subsystem_start_row = subsystem_end_row + 1
        output_name: str = configs[product_name]["output_name"]
        output_name = output_name.replace(".json", ".xls")
        excel_writer.save(output_name)

    @ classmethod
    def analysis(cls, product_name: str, product_dict: Dict[str, List[str]]):
        gn_info_file = configs["gn_info_file"]
        with open(gn_info_file, 'r', encoding='utf-8') as f:
            gn_info = json.load(f)
        query_order: Dict[str, List[str]
                          ] = configs[product_name]["query_order"]
        query_order["etc"] = configs["target_type"]
        rom_size_dict: Dict = dict()
        # prodcut_dict: {"so":["a.so", ...]}
        for t, l in product_dict.items():
            for f in l:  # 遍历所有文件
                # query_order: {"a":[static_library", ...]}
                find_flag = False
                type_list = query_order.get(t)
                _, base_name = os.path.split(f)
                size = os.path.getsize(f)
                if not type_list:
                    logging.warning(
                        f"'{t}' not found in query_order of the config.yaml")
                    break
                for tn in type_list:    # tn example: ohos_shared_library
                    output_dict: Dict[str, Dict] = gn_info.get(tn)  # 这个模板对应的所有可能编译产物
                    if not output_dict:
                        logging.warning(
                            f"'{tn}' not found in the {gn_info_file}")
                        continue
                    d = output_dict.get(base_name)
                    if not d:
                        continue
                    d["size"] = size
                    d["file_name"] = f.replace(project_path, "")
                    cls._put(d["subsystem_name"],
                             d["component_name"], d, rom_size_dict)
                    find_flag = True
                if not find_flag:
                    # fuzzy match
                    psesudo_gn, sub, com = cls._fuzzy_match(f)
                    if sub and com:
                        cls._put(sub, com, {
                            "subsystem_name": sub,
                            "component_name": com,
                            "psesudo_gn_path": psesudo_gn,
                            "description": "fuzzy match",
                            "file_name": f.replace(project_path, ""),
                            "size": size,
                        }, rom_size_dict)
                        find_flag = True
                if not find_flag:
                    cls._put("others", "others", {
                        "file_name": f.replace(project_path, ""),
                        "size": size,
                    }, rom_size_dict)
        with open(configs[product_name]["output_name"], 'w', encoding='utf-8') as f:
            json.dump(rom_size_dict, f, indent=4)
        cls._save_as_xls(rom_size_dict, product_name)


def main():
    if recollect_gn:
        RomAnalysisTool.collect_gn_info()
    product_dict: Dict[str, List[str]
                       ] = RomAnalysisTool.collect_product_info(product_name)
    RomAnalysisTool.analysis(product_name, product_dict)


if __name__ == "__main__":
    main()
    # t = os.listdir(
    #     "/home/aodongbiao/developtools_integration_verification/tools")
    # RomAnalysisTool._add_rest_dir(
    #     "/home/aodongbiao/developtools_integration_verification/tools", "", "rom_ram_analyzer/L2/pkgs", t)
    # print(t)
