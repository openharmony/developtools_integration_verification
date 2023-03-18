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
#


import itertools
import os
import re
import glob
from typing import *


def do_nothing(x: Any) -> Any:
    return x


class BasicTool:
    @classmethod
    def find_files_with_pattern(cls, folder: str, pattern: str = "/**", recursive: bool = True, apply_abs: bool = True,
                                real_path: bool = True, de_duplicate: bool = True, is_sort: bool = True,
                                post_handler: Callable[[List[str]], List[str]] = None) -> list:
        """
        根据指定paatern匹配folder下的所有文件，默认递归地查找所有文件
        folder：要查找的目录,会先经过cls.abspath处理(结尾不带/)
        pattern：要查找的模式,需要以/开头,因为会和folder拼接
        recursive：是否递归查找
        apply_abs：是否将路径转换为绝对路径
        real_path：如果是软链接，是否转换为真正的路径
        de_duplicate：是否去重
        is_sort：是否排序
        post_handler: 对文件进行额外处理的方法，参数为文件名的List，返回值为字符串列表
        FIXME 有可能会卡住,可能原因为符号链接
        """
        file_list = glob.glob(cls.abspath(folder)+pattern, recursive=recursive)
        if apply_abs:
            file_list = list(map(lambda x: cls.abspath(x), file_list))
        if real_path:
            file_list = list(map(lambda x: os.path.realpath(x), file_list))
        if de_duplicate:
            file_list = list(set(file_list))
        if is_sort:
            file_list = sorted(file_list, key=str.lower)
        if post_handler:
            file_list = post_handler(file_list)
        if folder in file_list:
            file_list.remove(folder)
        return file_list

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
    def abspath(cls, path: str) -> str:
        """
        将路径转换为绝对路径，如果有~，展开
        :param path: 要被转换的路径
        :return: 绝对路径
        """
        return os.path.abspath(os.path.expanduser(path))

    @classmethod
    def grep_ern(cls, pattern: str, path: str, include: str = str(), exclude: tuple = tuple(),
                 post_handler: Callable[[Text], Any] = do_nothing) -> Any:
        """
        执行grep命令来查找内容
        :param exclude: 不搜索path下的的exclude目录
        :param include: 指定要搜索的文件
        :param pattern: 使用pattern进行grep
        :param path: 搜索路径
        :param post_handler: 对grep的结果进行后处理
        :return: post_handler对grep结果进行处理后的结果
        TODO 将cls.execute用subprocess代替
        """
        cmd = f"grep -Ern '{pattern}' '{cls.abspath(path)}'"
        # E:启用正则表达式  r:递归搜索  n:显示行号
        if include:
            cmd += f" --include='{include}'"
        for e in exclude:
            cmd += f" --exclude-dir='{e}'"
        o = cls.execute(cmd)
        if post_handler:
            o = post_handler(o)
        return o

    @classmethod
    def execute(cls, cmd: str, post_processor: Callable[[Text], Text] = do_nothing) -> Any:
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
    res = BasicTool.grep_ern("^( *)ohos_prebuilt_shared_library", "/home/aodongbiao/oh", include="BUILD.gn", exclude=("/home/aodongbiao/oh/out","doc", ".ccache"), post_handler=lambda x: x.split('\n'))
    # print(res)
    for i in res:
        if "oh/out" in i:
            print(i)
