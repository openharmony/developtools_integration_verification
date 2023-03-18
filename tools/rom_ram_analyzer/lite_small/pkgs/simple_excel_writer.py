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

# This file contains a SimpleExcelWriter, which is a implemented based on xlwt for easy use.


import xlwt
from xlwt import Worksheet, Pattern as PTRN, Alignment as ALGT, Font as FT, XFStyle as XFSL
import typing
import logging
from typing import Optional
from collections.abc import Iterable


class SimpleExcelWriter:
    def __init__(self, default_sheet_name: str = "sheet1"):
        self.__book = xlwt.Workbook(encoding='utf-8', style_compression=0)
        self.__sheet_dict = {
            default_sheet_name: self.__book.add_sheet(
                sheetname=default_sheet_name, cell_overwrite_ok=True)
        }
        self.__sheet_pos = {
            default_sheet_name: (0, 0)  # 记录各个sheet页已经写到什么位置了，当前值为还没有写的
        }
        self.__default_sheet_name = default_sheet_name
        # 表头样式
        self.__head_style = XFSL()
        # 内容样式
        self.__content_style = XFSL()
        # 字体
        ft = FT()
        ft.bold = True

        # 设置背景颜色
        ptrn = PTRN()
        ptrn.pattern = PTRN.SOLID_PATTERN
        ptrn.pattern_fore_colour = 22  # 背景颜色

        # 居中对齐
        algmt = ALGT()
        algmt.horz = ALGT.HORZ_CENTER  # 水平方向
        algmt.vert = ALGT.VERT_CENTER  # 垂直方向
        self.__head_style.font = ft
        self.__head_style.alignment = algmt
        self.__head_style.pattern = ptrn
        self.__content_style.alignment = algmt

    def __increment_y(self, sheet_name: str, value: int = 1) -> int:
        if sheet_name in self.__sheet_pos.keys():
            x, y = self.__sheet_pos.get(sheet_name)
            y = y + value
            self.__sheet_pos[sheet_name] = (x, y)
            return y

    def __increment_x(self, sheet_name: str, value: int = 1) -> int:
        if sheet_name in self.__sheet_pos.keys():
            x, y = self.__sheet_pos.get(sheet_name)
            x = x + value
            self.__sheet_pos[sheet_name] = (x, 0)
            return x

    def append_line(self, content: list, sheet_name: str = None):
        sheet_name = self.__default_sheet_name if sheet_name is None else sheet_name
        if sheet_name not in self.__sheet_dict.keys():
            logging.error("sheet name '{}' not exist".format(sheet_name))
            return
        sheet: Worksheet = self.__sheet_dict.get(sheet_name)
        x, y = self.__sheet_pos.get(sheet_name)
        for ele in content:
            sheet.write(x, y, ele, style=self.__content_style)
            y = self.__increment_y(sheet_name)
        self.__increment_x(sheet_name)

    def write_merge(self, x0: int, y0: int, x1: int, y1: int, content: typing.Any,
                    sheet_name: str = None):
        sheet_name = self.__default_sheet_name if sheet_name is None else sheet_name
        if sheet_name not in self.__sheet_dict.keys():
            logging.error("sheet name '{}' not exist".format(sheet_name))
            return
        sheet: Worksheet = self.__sheet_dict.get(sheet_name)
        sheet.write_merge(x0, x1, y0, y1, content, style=self.__content_style)

    def set_sheet_header(self, headers: Iterable, sheet_name: str = None):
        """
        给sheet页设置表头
        """
        sheet_name = self.__default_sheet_name if sheet_name is None else sheet_name
        if sheet_name not in self.__sheet_dict.keys():
            logging.error("sheet name '{}' not exist".format(sheet_name))
            return
        x, y = self.__sheet_pos.get(sheet_name)
        if x != 0 or y != 0:
            logging.error(
                "pos of sheet '{}' is not (0,0). set_sheet_header must before write".format(sheet_name))
            return
        sheet: Worksheet = self.__sheet_dict.get(sheet_name)
        for h in headers:
            sheet.write(x, y, h, self.__head_style)
            y = self.__increment_y(sheet_name)
        self.__increment_x(sheet_name)

    def add_sheet(self, sheet_name: str, cell_overwrite_ok=True) -> Optional[xlwt.Worksheet]:
        if sheet_name in self.__sheet_dict.keys():
            logging.error("sheet name '{}' has exist".format(sheet_name))
            return
        self.__sheet_dict[sheet_name] = self.__book.add_sheet(
            sheetname=sheet_name, cell_overwrite_ok=cell_overwrite_ok)
        self.__sheet_pos[sheet_name] = (0, 0)
        return self.__sheet_dict.get(sheet_name)

    def save(self, file_name: str):
        self.__book.save(file_name)


if __name__ == '__main__':
    writer = SimpleExcelWriter(default_sheet_name="first")
    writer.add_sheet("second")
    writer.add_sheet("third")
    writer.set_sheet_header(["h", "m", "n"])
    writer.append_line([1, 2, 3])
    writer.append_line([2, 3, 4], "second")
    writer.append_line([3, 4, 5], "third")
    writer.append_line([3, 2, 1])
    writer.save("demo.xls")
