import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep)
import json
from utils import *

log_tag = 'read_acl_whitelist'


def read_json(path):
    set_log_content(LogLevel(2).name, log_tag, 'read {}'.format(path))
    if not os.path.exists(path):
        set_log_content(LogLevel(2).name, log_tag, '{} file not exits'.format(path))
        raise AclCheckException('{} file not exits'.format(path))
    try:
        with open(path, 'r') as f:
            file = f.read()
            return file
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag, e.msg)
        raise AclCheckException('{} failed to read the file.'.format(path))


def get_acl_dict(file):
    try:
        acls_dict = {}
        f = json.loads(file)
        for it in f:
            key = it.get('processName')
            values = it.get('acls')
            acls_dict[key] = values
        return acls_dict
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag, '{}'.format(e.msg))
        raise
