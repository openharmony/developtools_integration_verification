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
import math
import enum
import time
import logging
import threading
from apl_config import *

log_tag = 'common'

apl_file_log = logging.FileHandler(filename=APL_LOG_FILE, mode='a', encoding='utf-8')
fmt = logging.Formatter(fmt="%(asctime)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S %a')
apl_file_log.setFormatter(fmt)

# 定义日志
apl_logger = logging.Logger(name = 'apl_compare_log', level=logging.INFO)
apl_logger.addHandler(apl_file_log)

class ErrorType(enum.Enum):
    not_in_apl_table = 1
    apl_is_invalid = 2
	
class ApiLevel(enum.Enum):
	normal = 1
	system_basic = 2
	system_core = 3

class LogLevel(enum.Enum):
	Error = 1
	Info = 2

class AplCompareException(Exception):
    def __init__(self, msg):
        self.msg = msg

class AplCompareThread(threading.Thread):
    def __init__(self, func, args=()):
        super(AplCompareThread, self).__init__()
        self.func = func
        self.args = args
        self.result = None
    def run(self):
        self.result = self.func(*self.args)
    def get_result(self):
        threading.Thread.join(self)
        try:
            return self.result
        except Exception as e:
            apl_set_log_content(LogLevel(1).name, log_tag, '{}'.format(e.args[0]))
            return None

def apl_log(msg):
    # 写日志
    apl_logger.info(msg)

def apl_set_log_content(level, tag, msg):
    log_content = timestamp() + ' {}'.format(level) + ' [{}]'.format(tag) + ' {}'.format(msg)
    print(log_content)
    apl_log(log_content)
    return(log_content)

def set_error_record(name,error):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+' %(name)-50s: %(error)-50s\n'%{'name':name,'error':error}

def set_map(results):
    if results == None:
        return None
    res_map = {}
    for result in results:
        res_map[result[0]] = set_value(result[1:])
    return res_map
    
def set_value(result):
    value = []
    for res in result:
        if math.isnan(res):
            res = 0
        value.append(res)
    return value

def timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
