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
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep)
from read_device import *
from read_excel import *
from apl_config import *

def whitelist_check(apl, value, fields_from_whitelist):
    # True 包含在白名单内
    check = value in fields_from_whitelist.keys()
    is_pass = False
    if check and str(apl) == fields_from_whitelist[value]:
        is_pass = True
    return is_pass

def compare_hap_apl(fields_from_device, fields_from_whitelist):
    records = []
    log_tag = 'compare_hap_apl'
    hap_check = True
    for value in fields_from_device:
        apl = fields_from_device[value][0]
        if apl > 1:
            is_pass = whitelist_check(apl, value, fields_from_whitelist)
            info = 'bundleName = {} apl = {}'.format(value, str(apl))
            if is_pass == False:
                hap_check = False
                # info = value
                # info = 'bundleName = {} apl = {}'.format(value, str(apl))
                log_content = apl_set_log_content(LogLevel(1).name, log_tag, info)
                records.append(log_content)
            else:
              apl_set_log_content(LogLevel(2).name, log_tag, info)  
    return records, hap_check

def compare_native_apl(fields_from_device, fields_from_whitelist):
    records = []
    log_tag = 'compare_native_apl'
    native_check = True
    for value in fields_from_device:
        apl = fields_from_device[value][0]
        if apl > 2:
            info = 'processName = {} apl = {}'.format(value, str(apl))
            is_pass = whitelist_check(apl, value, fields_from_whitelist)
            if is_pass == False:
                native_check = False
                log_content = apl_set_log_content(LogLevel(1).name, log_tag, info)
                records.append(log_content)
            else:
                apl_set_log_content(LogLevel(2).name, log_tag, info)
    return records, native_check

def fields_compare_write_once(fields_from_device,fields_from_excel):
    records=[]
    for bundle_name in fields_from_device.keys():
        if bundle_name not in fields_from_excel.keys():
            record=(bundle_name,ErrorType(1).name)
            records.append(record)
            continue   
        
        fields=fields_from_device[bundle_name]
        standard_fields=fields_from_excel[bundle_name]
        if not isInvalid(fields,standard_fields):
            record=(bundle_name,ErrorType(2).name)
            records.append(record)
    print('Compare successful!')
    return records
    

def isInvalid(fields,standard_fields):
    if len(fields) == 1:
        return fields[0] <= standard_fields[0]
    
    for field, standard_field in fields, standard_fields:
        if field>standard_field:
            return False
    return True

def write_record(name,error):
    try:
        file = open(APL_RECORD_PATH,'a')
        err_record = set_error_record(name, error)
        file.write(err_record)
        file.close()
    except Exception as e:
        log_content=apl_set_log_content(str(s)) 
        apl_log(log_content)

def write_record_once(err_records,is_overwrite):
    try:
        file=open(APL_RECORD_PATH,is_overwrite)
        for record in err_records:
            err_record = set_error_record(record[0],record[1])
            file.write(err_record)
        file.close()
    except Exception as e:
        log_content=apl_set_log_content(str(e)) 
        apl_log(log_content)

def excel_thread():
    try:
        # settings={
        #     '	svn': SVN,
        #     'url': url_encode(SVN_URL),
        #     'user': USER,
        #     'pwd': PWD,
        #     'dir': FILE_PATH,
        # }
        # excel_file = FILE_PATH #svn_checkout(settings)
        log_tag = 'excel_thread'
        # if excel_file == None:
        #     apl_set_log_content(LogLevel(2).name, log_tag, 'svn_checkoutc failed') #raise
        # apl_from_excel = read_excel(excel_file, sheet = SHEET_NAME, cols = COLS)
        # path = PATH + 'APL基线标准v1.0.json'
        path = PATH + 'temp.json'
        apl_from_json = read_json(path)
        return apl_from_json
    except Exception as e:
        apl_set_log_content(LogLevel(1).name, log_tag, 'excel_thread catch error: {}'.format(e.args[0]))
        return None

def sql_thread(sn, sn2):
    try:
        print(DOWNLOAD_DB.format(sn)+' ' + SQL_SRC + ' ' + SQL_DES)
        print()
        log_tag = 'sql_thread'
        sql_file = download_from_device(DOWNLOAD_DB.format(sn), SQL_SRC, SQL_DES)
        if sql_file == None:
            raise
        query_hap_apl_thread = AplCompareThread(query_hap_apl, (sql_file, QUERY_HAP_APL))
        query_native_apl_thread = AplCompareThread(query_native_apl, (sql_file, QUERY_NATIVE_APL))
        
        query_hap_apl_thread.start()
        query_native_apl_thread.start()
        
        query_native_apl_thread.join()
        query_native_apl_thread.join()
        
        hap_apl_map = query_hap_apl_thread.get_result()
        native_apl_map = query_native_apl_thread.get_result()
        
        return hap_apl_map, native_apl_map
    except:
        apl_set_log_content(LogLevel(1).name, log_tag, 'download_from_device failed')
        return None,None

def apl_check_main(sn):
    try:
        log_tag = 'Main'
        apl_set_log_content(LogLevel(2).name, log_tag, '--------APL Check Begin!--------')
        excel_thr = AplCompareThread(excel_thread)
        sql_thr = AplCompareThread(sql_thread, (sn, sn))
        
        excel_thr.start()
        sql_thr.start()
        
        excel_thr.join()
        sql_thr.join()
        
        apl_from_excel = excel_thr.get_result()
        hap_apl_map, native_apl_map = sql_thr.get_result()

        if apl_from_excel == None or hap_apl_map == None or native_apl_map == None:
            raise
        hap_results, hap_check = compare_hap_apl(hap_apl_map, apl_from_excel)
        native_results, native_check = compare_native_apl(native_apl_map, apl_from_excel)
        write_record_once(hap_results, IS_OVERWRITE)
        write_record_once(native_results, 'a')
        if native_check == False or hap_check == False:
            apl_set_log_content(LogLevel(1).name, log_tag, '--------APL Check failed![hap = {}, native = {}] --------'.format(hap_check, native_check))
        apl_set_log_content(LogLevel(2).name, log_tag, '--------APL Check End! --------')
    except Exception as e:
        apl_set_log_content(LogLevel(1).name, log_tag, '--------APL Check failed![hap = False, native = False] --------')
        apl_set_log_content(LogLevel(1).name, log_tag, "{}".format(e.args[0]))

if __name__ == '__main__':
    try:
        sn = sys.argv[1]
    except:
        sn_list = []
        result = os.popen('hdc list targets')
        res = result.read()
        for line in res.splitlines():
            sn_list.append(line)
        sn = sn_list[0]
    apl_check_main(sn)
