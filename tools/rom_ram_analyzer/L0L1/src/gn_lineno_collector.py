from typing import *
import os
from collections import defaultdict
import preprocess
from pkgs.basic_tool import BasicTool
from pkgs.simple_yaml_tool import SimpleYamlTool


def gn_lineno_collect(match_pattern: str, project_path: str) -> DefaultDict[str, List[int]]:
    """
    在整个项目路径下搜索有特定target类型的BUILD.gn
    :param match_pattern: 进行grep的pattern，支持扩展的正则
    :param project_path: 项目路径（搜索路径）
    :return: {gn_file: [line_no_1, line_no_2, ..]}
    """
    config = SimpleYamlTool.read_yaml("config.yaml")
    # project_path = config.get("project_path")
    black_list = map(lambda x: os.path.join(
        project_path, x), config.get("black_list"))

    def handler(content: Text) -> List[str]:
        return list(filter(lambda y: len(y) > 0, list(map(lambda x: x.strip(), content.split("\n")))))

    grep_list = BasicTool.grep_ern(match_pattern, path=project_path, include="BUILD.gn", exclude=tuple(black_list),
                                   post_handler=handler)
    gn_line_dict: DefaultDict[str, List[int]] = defaultdict(list)
    for gl in grep_list:
        gn_file, line_no, _ = gl.split(":")
        gn_line_dict[gn_file].append(line_no)
    return gn_line_dict


if __name__ == '__main__':
    res = gn_lineno_collect(
        "^( *)ohos_shared_library\(.*?\)", BasicTool.abspath(project_path))
    for k, v in res.items():
        if "oh/out" in k:
            print("file={}, line_no={}".format(k, v))
