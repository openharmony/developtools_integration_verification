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

# import subprocess
# import pandas as pd
# import urllib.parse
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep)
from common import *
from apl_config import *
import json
log_tag = 'read_whitelist'

# # 全部文件夹检出（本地已经安装svn）
# def svn_checkout(settings):
#     try:
#         print(settings['url'])
#         print(settings['dir'])
#         os.chdir(settings['svn'])
#         cmd = 'svn export --force %(url)s %(dir)s --username %(user)s --password %(pwd)s'%settings
#         p =  subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
#         stdout,stderr = p.communicate()
#         print(stderr)
#         if stderr != b'':
#             raise AplCompareException(str(stderr,'utf-8').replace('\r\n','\t'))
#         apl_set_log_content(LogLevel(2).name, log_tag, '{} export successful!'.format(settings['dir']))
#         return settings['dir']
#     except Exception as e:
#         apl_set_log_content(LogLevel(1).name, log_tag, "{}".format(e.msg))
#         return None
#
# #url编码
# def url_encode(url):
#     partions=url.split("/",3)
#     encode_url=partions[0]
#     partions[-1]=urllib.parse.quote(partions[-1])
#     for partion in partions[1:]:
#         encode_url=encode_url+'/'+partion
#     return encode_url
#
# def read_excel(file, sheet, cols):
#     try:
#         df = pd.read_excel(file, sheet_name = sheet, usecols = cols)
#         data_list = df.values.tolist()
#         apl_map = set_map(data_list)
#         apl_set_log_content(LogLevel(2).name, log_tag, '{} read successful!'.format(file))
#         return apl_map
#     except (ValueError,FileNotFoundError) as e:
#         apl_set_log_content(LogLevel(1).name, log_tag, "{}".format(e.msg))
#         return None
#
        
def read_json(path):
    try:
        with open(path, 'r') as f:
            file = f.read()
            data_list = json.loads(file)
            res_dict = set_dict(data_list)
            return res_dict
    except Exception as e:
        apl_set_log_content(LogLevel(1).name, log_tag, '{}'.format(e.msg))
        return None

def set_dict(data_list: list()):
    res_dict = {}    
    for res in data_list:
        res_dict[res['bundle&processName']] = res['apl']
    return res_dict    