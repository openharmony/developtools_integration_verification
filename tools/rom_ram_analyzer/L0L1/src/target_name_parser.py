import sys
from typing import *

import preprocess
from pkgs.basic_tool import BasicTool


class TargetNameParser:
    @classmethod
    def single_parser(cls, paragraph: Text) -> str:
        """
        查找类似shared_library("xxx")这种括号内只有一个参数的target的名称
        :param paragraph: 要解析的段落
        :return: target名称，如果是变量，不会对其进行解析
        """
        return BasicTool.re_group_1(paragraph, r"\w+\((.*)\)")

    @classmethod
    def second_parser(cls, paragraph: Text) -> str:
        """
        查找类似target("shared_library","xxx")这种的target名称（括号内第二个参数）
        :param paragraph: 要解析的段落
        :return: target名称，如果是变量，不会的其进行解析
        """
        return BasicTool.re_group_1(paragraph, r"\w+\(.*?, *(.*?)\)")
