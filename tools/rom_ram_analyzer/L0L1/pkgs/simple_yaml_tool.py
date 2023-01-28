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