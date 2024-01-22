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

from subprocess import run
import os
import sqlite3

import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep)
from common import *
from apl_config import *
log_tag = 'read_device'

#从设备中导出数据库
def download_from_device(cmd,sql_src,sql_des):
    download_cmd=cmd+' '+sql_src+' '+sql_des
    apl_set_log_content(LogLevel(2).name, log_tag, 'database start downloading!')
    try:
        result = os.popen(download_cmd)
        stdout = result.read()
        print(stdout)
        if 'Fail' in stdout:
            raise AplCompareException(stdout.replace('\n\n','').replace('[Fail]', ''))     
        #sql_file=sql_des+'\\'+sql_src.split('/').pop()
        sql_file = sql_des+sql_src.split('/').pop()
        apl_set_log_content(LogLevel(2).name, log_tag, '{} download successful!'.format(sql_file))
        return sql_file
    except Exception as e:
        apl_set_log_content(LogLevel(1).name, log_tag, '{}'.format(e.msg))
        return None


def sql_connect(db):
    try:
        if not os.path.exists(db):
            raise AplCompareException('{} is not exists!'.format(db))
        conn = sqlite3.connect(db)
        return conn
    except AplCompareException as e:
        apl_set_log_content(LogLevel(1).name, log_tag, '{}'.format(e.msg))
        return None

#数据库语句查询 
def query_records(db,sql):
    log_content = ''
    try:
        conn = sql_connect(db)
        if conn == None:
            raise AplCompareException('{} cannot connect!'.format(db))
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()      
        conn.close()
        apl_set_log_content(LogLevel(2).name, log_tag, '"{}" query successful!'.format(sql))
        return results
    except sqlite3.OperationalError as e:
        apl_set_log_content(LogLevel(2).name, log_tag, 'database {}'.format(e.args[0]))
        return None
    except AplCompareException as e:
        apl_set_log_content(LogLevel(1).name, log_tag, '{}'.format(e.msg))
        return None
    
#查询hap_token_info_table中的bundle_name和apl 
def query_hap_apl(db,sql):
    results = query_records(db, sql)
    return set_map(results)

#查询native_token_info_table中的process_name和apl
def query_native_apl(db,sql):
    results = query_records(db, sql)
    return set_map(results)
