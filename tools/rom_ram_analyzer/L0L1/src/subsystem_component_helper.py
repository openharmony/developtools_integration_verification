import os
import logging
import json
import re
from typing import *
from pkgs.gn_common_tool import GnCommonTool


class SubsystemComponentNameFinder:
    @classmethod
    def _find_subsystem_component_from_bundle(cls, gn_path: str, stop_tail: str = "home") -> Tuple[str, str]:
        """
        根据BUILD.gn的全路径，一层层往上面查找bundle.json文件，
        并从bundle.json中查找component_name和subsystem
        """
        filename = "bundle.json"
        subsystem_name = str()
        component_name = str()
        if stop_tail not in gn_path:
            logging.error("{} not in {}".format(stop_tail, gn_path))
            return subsystem_name, component_name
        if os.path.isfile(gn_path):
            gn_path, _ = os.path.split(gn_path)
        while not gn_path.endswith(stop_tail):
            bundle_path = os.path.join(gn_path, filename)
            if not os.path.isfile(bundle_path):  # 如果该文件不在该目录下
                gn_path, _ = os.path.split(gn_path)
                continue
            with open(bundle_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                try:
                    component_name = content["component"]["name"]
                    subsystem_name = content["component"]["subsystem"]
                except KeyError:
                    logging.warning(
                        "not found component/name or component/subsystem in bundle.json")
                finally:
                    break
        return subsystem_name, component_name

    @classmethod
    def _parse_subsystem_component(cls, content: str) -> Tuple[Text, Text]:
        """
        从字符串中提取subsystem_name和component_name字段
        """
        subsystem_name = str()
        component_name = str()
        subsystem = re.search(r"subsystem_name *=\s*(\S*)", content)
        part = re.search(r"component_name *=\s*(\S*)", content)
        if subsystem:
            subsystem_name = subsystem.group(1)
        if part:
            component_name = part.group(1)
        return subsystem_name, component_name

    @classmethod
    def find_part_subsystem(cls, gn_file: str, project_path: str) -> Tuple[Text, Text]:
        """
        查找gn_file对应的component_name和subsystem
        如果在gn中找不到，就到bundle.json中去找
        FIXME 一个gn文件中的target不一定属于同一个component,比如hap包
        """
        part_var_flag = False  # 标识这个变量从gn中取出的原始值是不是变量
        subsystem_var_flag = False
        var_list = list()
        with open(gn_file, 'r', encoding='utf-8') as f:
            subsystem_name, component_name = cls._parse_subsystem_component(f.read())
        if len(component_name) != 0 and GnCommonTool.is_gn_variable(component_name):
            part_var_flag = True
            var_list.append(component_name)

        if len(subsystem_name) != 0 and GnCommonTool.is_gn_variable(subsystem_name):
            subsystem_var_flag = True
            var_list.append(subsystem_name)

        if part_var_flag and subsystem_var_flag:
            component_name, subsystem_name = GnCommonTool.find_variables_in_gn(
                tuple(var_list), gn_file, project_path)
        elif part_var_flag:
            component_name = GnCommonTool.find_variables_in_gn(
                tuple(var_list), gn_file, project_path)[0]
        elif subsystem_var_flag:
            subsystem_name = GnCommonTool.find_variables_in_gn(
                tuple(var_list), gn_file, project_path)[0]
        if len(component_name) != 0 and len(subsystem_name) != 0:
            return component_name, subsystem_name
        # 如果有一个没有找到，就要一层层去找bundle.json文件
        t_component_name, t_subsystem_name = cls._find_subsystem_component_from_bundle(
            gn_file, stop_tail=project_path)
        if len(component_name) == 0:
            component_name = t_component_name
        if len(subsystem_name) == 0:
            subsystem_name = t_subsystem_name
        return component_name, subsystem_name
