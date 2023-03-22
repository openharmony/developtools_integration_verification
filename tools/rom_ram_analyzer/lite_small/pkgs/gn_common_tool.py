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

# This file contains some Classes for gn's BUILD.gn

import os
import logging
import re
import ast
import json
import collections
from typing import *
if __name__ == '__main__':
    from basic_tool import BasicTool
else:
    from pkgs.basic_tool import BasicTool


class GnCommonTool:
    """
    处理BUILD.gn文件的通用方法
    """

    @classmethod
    def _find_gn_variable_list(cls, content: str) -> List:
        """
        获取s中${xxx}或$xxx形式的gn变量
        :param content: 待查找的字符串
        :param sep: 分隔符，使用本分隔符将内容进行分隔然后逐一查找
        :return: 变量名及其符号，eg：${abc}、$abc
        :FIXME 没有对a = 'a' b = a中的b这种形式进行处理
        """
        result = list()
        splited = content.split(os.sep)
        patern = re.compile(r"\${.*?}")
        for item in splited:
            m = re.findall(patern, item)
            result.extend(m)
            if len(m) == 0 and "$" in item:
                item = item.strip('"')
                result.append(item[item.index("$"):])
        return result

    @classmethod
    def is_gn_variable(cls, target: str, quote_processed: bool = False):
        """
        判断target是否是gn中的变量:
        规则：如果是quote_processed is False，则没有引号均认为是变量，有引号的情况下，如果是"$xxx"或${xx}的模式，则认为xxx是变量；
        如果quote_processed is True，则只要$开头就认为是变量
        b = "xxx"
        c = b
        c = "${b}"
        "$p"
        :param target: 要进行判断的字符串对象
        :param quote_processed: 引号是否已经去除
        :return: target是否为gn中的变量
        """
        target = target.strip()
        if quote_processed:
            return target.startswith("$")
        if target.startswith('"') and target.endswith('"'):
            target = target.strip('"')
            if target.startswith("${") and target.endswith("}"):
                return True
            elif target.startswith("$"):
                return True
            return False
        else:
            return True

    @classmethod
    def contains_gn_variable(cls, s: str, quote_processed: bool = False):
        """
        判断字符串s中是否包含gn变量
        """
        return cls.is_gn_variable(s, quote_processed) or ("$" in s)

    # 给__find_variables_in_gn用的，减少io
    __var_val_mem_dict = collections.defaultdict(str)

    @classmethod
    def find_variables_in_gn(cls, var_name_tuple: tuple, path: str, stop_tail: str = "home", use_cache: bool = False) -> \
            List[str]:
        """
        同时查找多个gn变量的值
        var_name_tuple：变量名的tuple，变量名应是未经过处理后的，如：
        xxx
        "${xxx}"
        "$xxx"
        :param var_name_tuple: 待查找的变量名的列表
        :param path: 变量名所在文件的路径
        :param stop_tail: 当path以stop_tail结尾时，停止查找
        :param use_cache: 是否使用缓存
        :return: 变量值的列表
        """
        if os.path.isfile(path):
            path, _ = os.path.split(path)
        var_val_dict = collections.defaultdict(str)
        not_found_count = len(var_name_tuple)
        if use_cache:
            for var in var_name_tuple:
                val = GnCommonTool.__var_val_mem_dict[var]
                if val:
                    not_found_count -= 1
                var_val_dict[var] = val
        while (stop_tail in path) and not_found_count:
            for v in var_name_tuple:
                pv = v.strip('"').lstrip("${").rstrip('}')
                # 先直接grep出pv *= *\".*?\"的
                # 然后排除含有$符的
                # 再取第一个
                # 最后只取引号内的
                cmd = fr"grep -Ern '{pv} *= *\".*?\"' --include=*.gn* {path} | grep -Ev '\$' " \
                      r"| head -n 1 | grep -E '\".*\"' -wo"
                output = BasicTool.execute(cmd, lambda x: x.strip().strip('"'))
                # backup:end
                if not output:
                    continue
                not_found_count -= 1
                var_val_dict[v] = output
                GnCommonTool.__var_val_mem_dict[v] = output
            path, _ = os.path.split(path)
        return list(var_val_dict.values())

    @classmethod
    def replace_gn_variables(cls, s: str, gn_path: str, stop_tail: str) -> str:
        """
        替换字符串中的gn变量名为其值,注意,没有对s是否真的包含gn变量进行验证
        :param s: 待替换的字符串
        :param gn_path: 字符串所在的gn文件
        :param stop_tail: 当变量查找到stop_tail目录时停止
        :return: 将变量替换为其值的字符串
        """
        variable_list = GnCommonTool._find_gn_variable_list(s)
        if len(variable_list) == 0:
            return s
        value_list = GnCommonTool.find_variables_in_gn(
            tuple(variable_list), path=gn_path, stop_tail=stop_tail)
        for k, v in dict(zip(variable_list, value_list)).items():
            s = s.replace(k, v)
        return s

    @classmethod
    def find_values_of_variable(cls, var_name: str, path: str, stop_tail: str = "home") -> list:
        """
        查找变量的值，如果有多个可能值，全部返回
        :param var_name: 变量名
        :param path: 变量名所在的文件
        :param stop_tail: 当变量查找到stop_tail目录时停止
        :return: 该变量的可能值
        """
        if os.path.isfile(path):
            path, _ = os.path.split(path)
        result = list()
        v = var_name.strip('"').lstrip("${").rstrip('}')
        while stop_tail in path:
            cmd = fr"grep -Ern '^( *){v} *= *\".*?\"' --include=*.gn* {path}"
            output = os.popen(cmd).readlines()
            path = os.path.split(path)[0]
            if not output:
                continue
            for line in output:
                line = line.split('=')[-1].strip().strip('"')
                if len(line) == 0:
                    continue
                result.append(line)
            break
        return result


class GnVariableParser:
    @classmethod
    def string_parser(cls, var: str, content: str) -> str:
        """
        解析值为字符串的变量,没有对引号进行去除,如果是a = b这种b为变量的,则无法匹配
        :param content: 要进行解析的内容
        :param var: 变量名
        :return: 变量值[str]
        """
        result = BasicTool.re_group_1(
            content, r"{} *= *[\n]?(\".*?\")".format(var), flags=re.S | re.M)
        return result

    @classmethod
    def list_parser(cls, var: str, content: str) -> List[str]:
        """
        解析值为列表的变量，list的元素必须全为数字或字符串,且没有对引号进行去除,如果是a = b这种b为变量的,则无法匹配
        :param var: 变量名
        :param content: 要进行
        :return: 变量值[List]
        """
        result = BasicTool.re_group_1(
            content, r"{} *= *(\[.*?\])".format(var), flags=re.S | re.M)
        result = ast.literal_eval(result.strip())
        return result


if __name__ == '__main__':
    cc = \
        """
        target("shared_library", "mmp"){
            xxx
        }
        
        ohos_shared_library("pinauthservice") {
          sources = [
            "//base/useriam/pin_auth/services/modules/driver/src/pin_auth_driver_hdi.cpp",
            "//base/useriam/pin_auth/services/modules/driver/src/pin_auth_interface_adapter.cpp",
            "//base/useriam/pin_auth/services/modules/executors/src/pin_auth_executor_callback_hdi.cpp",
            "//base/useriam/pin_auth/services/modules/executors/src/pin_auth_executor_hdi.cpp",
            "//base/useriam/pin_auth/services/modules/inputters/src/i_inputer_data_impl.cpp",
            "//base/useriam/pin_auth/services/modules/inputters/src/pin_auth_manager.cpp",
            "//base/useriam/pin_auth/services/sa/src/pin_auth_service.cpp",
          ]
        
          configs = [
            ":pin_auth_services_config",
            "//base/useriam/user_auth_framework/common:iam_log_config",
            "//base/useriam/user_auth_framework/common:iam_utils_config",
          ]
        
          deps = [
            "//base/useriam/pin_auth/frameworks:pinauth_ipc",
            "//third_party/openssl:libcrypto_shared",
          ]
        
          external_deps = [
            "access_token:libaccesstoken_sdk",
            "c_utils:utils",
            "drivers_interface_pin_auth:libpin_auth_proxy_1.0",
            "hisysevent_native:libhisysevent",
            "hiviewdfx_hilog_native:libhilog",
            "ipc:ipc_core",
            "safwk:system_ability_fwk",
            "user_auth_framework:userauth_executors",
          ]
          t = [
          1,
          2,
          3
          ]
          tt = [
          aaa,
          bbb,
          ccc
          ]
          remove_configs = [ "//build/config/compiler:no_exceptions" ]
        
          subsystem_name = "useriam"
          part_name = "pin_auth"
        }"""
    s = """
updater_usb_init_cfg_path = "//base/startup/init/services/etc/init.usb.cfg"
updater_init_usb_configfs_path_cfg =
    "//drivers/peripheral/usb/cfg/init.usb.configfs.cfg"
updater_faultloggerd_cfg = 
"//base/hiviewdfx/faultloggerd/services/config/faultloggerd.cfg"
updater_hilog_cfg = "//base/hiviewdfx/hilog/services/hilogd/etc/hilogd.cfg"

ohos_prebuilt_etc("updater_hilog.cfg") {
source = "${updater_hilog_cfg}"
install_images = [ "updater" ]
part_name = "updater"
}
"""
    s = "\"${updater_faultloggerd_cfg}\""
    print(GnCommonTool.contains_gn_variable(s))
    ...
