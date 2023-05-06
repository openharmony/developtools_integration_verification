
if __name__ == '__main__':
    from basic_tool import BasicTool
else:
    from pkgs.basic_tool import BasicTool
from typing import Dict, Any
import unittest
import json
import logging

class RomRamBaselineCollector:
    """collect baseline of rom and ram from bundle.json
    """
    @classmethod
    def _put(cls, result_dict: Dict, subsystem_name: str, component_name: str, rom_size: str, ram_size: str, bundle_path:str) -> None:
        if not result_dict.get(subsystem_name):
            result_dict[subsystem_name] = dict()
        result_dict[subsystem_name][component_name] = dict()
        result_dict[subsystem_name][component_name]["rom"] = rom_size
        result_dict[subsystem_name][component_name]["ram"] = ram_size
        result_dict[subsystem_name][component_name]["bundle.json"] = bundle_path

    @classmethod
    def collect(cls, oh_path: str) -> Dict[str, Dict]:
        def post_handler(x:str)->list:
            x = x.split("\n")
            y = [item for item in x if item]
            return y
        bundle_list = BasicTool.execute(cmd=f"find {oh_path} -name bundle.json", post_processor=post_handler)
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
                    logging.warning(f"subsystem=\"{subsystem_name}\", rom=\"{rom_baseline}\", ram=\"{ram_baseline}\" in {bundle}")
                cls._put(rom_ram_baseline_dict, subsystem_name, component_name, rom_baseline, ram_baseline, bundle)
        return rom_ram_baseline_dict


class TestRomRamBaselineCollector(unittest.TestCase):

    def test_collect(self):
        RomRamBaselineCollector.collect("/mnt/data/aodongbiao/codechecker_oh")
        ...
    
    def test_bundle(self):
        def post_handler(x:str)->list:
            x = x.split("\n")
            y = [item for item in x if item]
            return y
        oh_path = "/mnt/data/aodongbiao/codechecker_oh"
        bundle_list = BasicTool.execute(cmd=f"find {oh_path} -name bundle.json", post_processor=post_handler)
        print(bundle_list)
    


if __name__ == '__main__':

    unittest.main()
