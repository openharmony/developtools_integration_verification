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
import os
import platform
import time

# 系统分隔符
SYS_SEQ = os.sep
# 系统平台
SYS_PLATFORM = platform.system()

PATH = os.path.dirname(os.path.realpath(__file__)) + SYS_SEQ
# 脚本的执行日志
LOG_FILE = PATH + SYS_SEQ + "native_sa.log"
# 设备上生成的token info 文件名
TOKEN_INFO_NAME = 'token_info_'+ str(time.time_ns()) +'_{}.txt'
# 设备上生成文件存放位置
TOKEN_INFO_URL = '/data/{}'.format(TOKEN_INFO_NAME)
# 设备上文件生成命令
GENERATING_TOKEN_INFO_COMMAND = 'hdc -t {} shell atm dump -t > {}'
# 下载token info 文件存放路径
DOWNLOAD_TOKEN_INFO_URL = PATH + TOKEN_INFO_NAME
# 文件下载命令
DOWNLOAD_TOKEN_INFO_COMMAND = 'hdc -t {} file recv {} {}'
# 删除设备上的文件命令
CLEAR_TOKEN_INFO_FILE = 'hdc -t {} shell rm -rf {}'
