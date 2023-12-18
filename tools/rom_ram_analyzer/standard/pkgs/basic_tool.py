import sys
import typing
import os
import glob
import re
from pathlib import Path
from typing import *


def unit_adaptive(size: int) -> str:
    unit_list = ["Byte", "KB", "MB", "GB"]
    index = 0
    while index < len(unit_list) and size >= 1024:
        size /= 1024
        index += 1
    if index == len(unit_list):
        index = len(unit_list) - 1
        size *= 1024
    return str(round(size, 2)) + unit_list[index]


class BasicTool:
    @classmethod
    def match_paragraph(cls, content: str, start_pattern: str = r"\w+\(\".*?\"\) *{", end_pattern: str = "\}") -> \
            Iterator[re.Match]:
        """
        匹配代码段，支持单行
        注意：ptrn中已经包含前面的空格，所以start_pattern中可以省略
        :param content: 被匹配的字符串
        :param start_pattern: 模式的开头
        :param end_pattern: 模式的结尾
        :return: 匹配到的段落的迭代器
        """
        ptrn = r'^( *){s}(?#匹配开头).*?(?#中间非贪婪)\1(?#如果开头前面有空格,则结尾的前面应该有相同数量的空格)?{e}$(?#匹配结尾)'.format(
            s=start_pattern, e=end_pattern)
        ptrn = re.compile(ptrn, re.M | re.S)
        result = re.finditer(ptrn, content)
        return result

    @classmethod
    def find_all_files(cls, folder: str, real_path: bool = True, apply_abs: bool = True, de_duplicate: bool = True,
                       p_filter: typing.Callable = lambda x: True) -> list:
        filepath_list = set()
        for root, _, file_names in os.walk(folder):
            filepath_list.update(
                [os.path.abspath(os.path.realpath(
                    os.path.join(root, f) if real_path else os.path.join(root, f))) if apply_abs else os.path.relpath(
                    os.path.realpath(os.path.join(root, f) if real_path else os.path.join(root, f))) for f in file_names
                 if p_filter(os.path.join(root, f))])
        if de_duplicate:
            filepath_list = set(filepath_list)
        filepath_list = sorted(filepath_list, key=str.lower)
        return filepath_list

    @classmethod
    def get_abs_path(cls, path: str) -> str:
        return os.path.abspath(os.path.expanduser(path))

    @classmethod
    def re_group_1(cls, content: str, pattern: str, **kwargs) -> str:
        """
        匹配正则表达式，如果有匹配到内容，返回group(1)的内容
        :param content: 要被匹配的内容
        :param pattern: 进行匹配的模式
        :return: 匹配到的结果（group(1)）
        TODO 对（）的检查应该更严格
        """
        if not (r'(' in pattern and r')' in pattern):
            raise ValueError("parentheses'()' must in the pattern")
        result = re.search(pattern, content, **kwargs)
        if result:
            return result.group(1)
        return str()

    @classmethod
    def execute(cls, cmd: str, post_processor: Callable[[Text], Text] = lambda x: x) -> Any:
        """
        封装popen，返回标准输出的列表
        :param post_processor: 对执行结果进行处理
        :param cmd: 待执行的命令
        :return: 经处理过后的字符串列表

        """
        output = os.popen(cmd).read()
        output = post_processor(output)
        return output


if __name__ == '__main__':
    for i in BasicTool.find_all_files(".", apply_abs=False):
        print(i)
