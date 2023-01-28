from typing import *
from abc import ABC, abstractmethod
import copy
import logging
import preprocess
from pprint import pprint
from pkgs.simple_yaml_tool import SimpleYamlTool

_config = SimpleYamlTool.read_yaml("./config.yaml")


class BasePostHandler(ABC):
    @abstractmethod
    def run(self, unit: Dict[str, AnyStr]) -> str:
        ...

    def __call__(self, unit: Dict[str, AnyStr]) -> str:
        return self.run(unit)


class DefaultPostHandler(BasePostHandler):
    def run(self, unit: Dict[str, AnyStr]):
        return unit["output_name"]


class HAPPostHandler(BasePostHandler):
    """
    for ohos_hap"""

    def run(self, unit: Dict[str, AnyStr]):
        extension = _config.get("default_extension").get("app")
        gn_hap_name = unit.get("hap_name")
        if gn_hap_name:
            return gn_hap_name+extension
        return unit["output_name"]+extension


class SOPostHandler(BasePostHandler):
    """
    for shared_library"""

    def run(self, unit: Dict[str, AnyStr]):
        output_name = unit["output_name"]
        prefix = _config.get("default_prefix").get("shared_library")
        if unit.get("extension"):
            extension = unit.get("extension")
        else:
            extension = _config.get("default_extension").get("shared_library")
        if output_name.startswith(prefix):
            return output_name+extension
        return prefix+output_name+extension


class APostHandler(BasePostHandler):
    """
    for static library"""

    def run(self, unit: Dict[str, AnyStr]):
        output_name = unit["output_name"]
        prefix = _config.get("default_prefix").get("static_library")
        extension = _config.get("default_extension").get("static_library")
        if output_name.startswith(prefix):
            return output_name+extension
        return prefix+output_name+extension


class LiteLibPostHandler(BasePostHandler):
    """
    for lite_library"""

    def run(self, unit: Dict[str, AnyStr]):
        tp = unit["real_target_type"]
        output_name = unit["output_name"]
        if tp == "static_library":
            prefix = _config.get("default_prefix").get("static_library")
            extension = _config.get("default_extension").get("static_library")
        elif tp == "shared_library":
            prefix = _config.get("default_prefix").get("shared_library")
            extension = _config.get("default_extension").get("shared_library")
        else:
            prefix = str()
            extension = str()
        if output_name.startswith(prefix):
            return output_name+extension
        return prefix+output_name+extension


class LiteComponentPostHandler(BasePostHandler):
    """
    for lite_component"""

    def run(self, unit: Dict[str, AnyStr]):
        tp = unit["real_target_type"]
        output_name = unit["output_name"]
        extension = unit.get("output_extension")
        if tp == "shared_library":
            prefix = _config.get("default_prefix").get("shared_library")
            extension = _config.get("default_extension").get("shared_library")
        else:
            if tp != "executable":
                unit["description"] = "virtual node"
            prefix = str()
            extension = str()
        return prefix+output_name+extension

"""
==========================分割线===========================
"""

def LiteLibS2MPostHandler(unit:Dict, result_dict:Dict)->None:
    rt = unit.get("real_target_type")
    new_unit = copy.deepcopy(unit)
    if rt == "shared_library":
        new_unit["real_target_type"] = "static_library"
        k = LiteLibPostHandler()(new_unit)
        new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_unit
    elif rt == "static_library":
        new_unit["real_target_type"] = "shared_library"
        k = LiteLibPostHandler()(new_unit)
        new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_unit
    else:
        logging.warning(f"target type should be 'shared_library' or 'static_library', but got '{rt}'")
        new_unit["real_target_type"] = "shared_library"
        k = LiteLibPostHandler()(new_unit)
        new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_unit
        
        new_new_unit = copy.deepcopy(unit)
        new_new_unit["real_target_type"] = "static_library"
        k = LiteLibPostHandler()(new_new_unit)
        new_new_unit["description"] = "may not exist"
        result_dict["lite_library"][k] = new_new_unit


if __name__ == '__main__':
    h = SOPostHandler()
    pseudo_d = {"output_name": "libmmp"}
    print(h(pseudo_d))
