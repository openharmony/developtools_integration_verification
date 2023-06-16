import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep)
from utils import *

log_tag = 'resolve_token_info'


def check_and_get(file: list):
    nativeAcls = {}
    try:
        set_log_content(LogLevel(2).name, log_tag,
                        '-------------------------- invalidPermList check begin --------------------------')
        check_pass = True
        processName = 'xxxxxxxx'
        for it in file:
            if it.find('processName') != -1:
                processName = it.replace(',', '').split(':')[1].split('"')[1]
            elif it.find('invalidPermList') != -1:
                check_pass = False
                msg = 'invalidPermList information is detected in processName = {}'.format(processName)
                set_log_content(LogLevel(2).name, log_tag, msg)
            elif check_pass and it.find('nativeAcls') != -1:
                bb = it.split(':')
                if bb[1].split('"')[1].__len__() == 0:
                    continue
                permissionNameList = bb[1].split('"')[1].split(',')
                nativeAcls[processName] = permissionNameList
        if check_pass == False:
            raise AclCheckException('-------------------------- The invalidPermList check failed --------------------------')
        else:
            set_log_content(LogLevel(2).name, log_tag,
                            '-------------------------- The invalidPermList check successful --------------------------')
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag, e.msg)
        raise
    return nativeAcls


def clear_token_info_txt(path):
    try:
        os.remove(path)
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag, e.msg)


def read_txt(path):
    set_log_content(LogLevel(2).name, log_tag, 'read {}'.format(path))
    if not os.path.exists(path):
        set_log_content(LogLevel(2).name, log_tag, '{} file not exits'.format(path))
        raise AclCheckException('{} file not exits!'.format(path))
    try:
        with open(path, 'r') as f:
            file = f.readlines()
            return file
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag, e.msg)
        raise AclCheckException('{} failed to read the file.'.format(path))
