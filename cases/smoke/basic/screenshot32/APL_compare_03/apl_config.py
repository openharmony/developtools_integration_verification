# -*- coding: utf-8 -*-
# Copyright (c) 2023 Huawei Device Co., Ltd.
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
#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
# PATH='D:\\repo_test\\APL_compare_02\\'
# PATH=os.getcwd()+'/'
PATH = os.path.dirname(os.path.realpath(__file__)) + os.sep
# read_excel.py
'''
SHEET_NAME：excel中的表名，中英文都可
COLS：excel中的列号，从0开始
SVN：SVN的安装目录下/bin目录（SVN在环境变量中的位置）
SVN_URL：excel文件对应的url
USER：svn的用户名
PWD：svn的密码
FILE_PATH：本地下载文件的路径
'''
SHEET_NAME = "Sheet1"
COLS = [1, 3]

SVN = 'D:/TortoiseSVN/bin'
SVN_URL = 'https://PMAIL_2140981.china.huawei.com/svn/test测试/01 目录/01_1 目录/APL基线标准v1.0.xlsx'
USER = 'hhhhs'
PWD = '123456'
FILE_PATH = PATH + SVN_URL.split('/')[-1]

# read_device.py
'''
SQL_SRC：设备上的数据库路径
SQL_DES：本地下载文件路径
DOWNLOAD_DB：从设备下载的hdc命令
QUERY_HAP_APL：查询HAP APL的sql语句（查询多列可以依次添加字段，添加字段的顺序为比较时的字段优先级）
QUERY_NATIVE_APL：查Native APL的sql语句
'''
SQL_SRC = " /data/service/el1/public/access_token/access_token.db"
SQL_DES = PATH
DOWNLOAD_DB = "hdc -t {} file recv"
QUERY_HAP_APL = "select bundle_name,apl from hap_token_info_table"
QUERY_NATIVE_APL = "select process_name,apl from native_token_info_table"

'''
APL_LOG_FILE：执行脚本的日志信息
APL_RECORD_PATH：APL对比记录的日志信息
IS_OVERWRITE：是否覆盖之前的APL日志，w表示覆盖，a表示追加
'''
APL_LOG_FILE = PATH + 'apl_compare.log'
APL_RECORD_PATH = PATH + 'apl_record.txt'
IS_OVERWRITE = 'w'
