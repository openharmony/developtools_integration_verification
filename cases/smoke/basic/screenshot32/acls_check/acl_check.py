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
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep)
from resolve_token_info import *
from read_acl_whitelist import *

log_tag = 'acl_check'


def whitelist_check(whitelist, acls):
    try:
        set_log_content(LogLevel(2).name, log_tag + '->whitelist_check',
                        '-------------------------- Trustlist Verification begin --------------------------')
        check_pass = True
        for k, v in acls.items():
            if k in whitelist.keys():
                temp = whitelist[k]
                for acl in v:
                    if acl not in temp:
                        check_pass = False
                        set_log_content(LogLevel(2).name, log_tag, log_tag + '->whitelist_check',
                                        'precessName = {} the acl = {} trustlist is not configured.'.format(k, acl))
            else:
                check_pass = False
                set_log_content(LogLevel(2).name, log_tag + '->whitelist_check', 'precessName = {} the acls = {} trustlist is not configured.'.format(k, v))
        if check_pass == False:
            raise AclCheckException(
                '-------------------------- Trustlist Verification failed --------------------------')
        else:
            set_log_content(LogLevel(2).name, log_tag + '->whitelist_check',
                        '-------------------------- Trustlist Verification successful --------------------------')
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag + '->whitelist_check', e.msg)
        raise


def main(sn):
    set_log_content(LogLevel(2).name, log_tag,
                    '-------------------------- ACL check begin --------------------------')
    try:
        hdc_command(GENERATING_TOKEN_INFO_COMMAND.format(sn, TOKEN_INFO_URL.format(sn)))
        hdc_command(DOWNLOAD_TOKEN_INFO_COMMAND.format(sn, TOKEN_INFO_URL.format(sn), DOWNLOAD_TOKEN_INFO_URL.format(sn)))
        hdc_command(CLEAR_TOKEN_INFO_FILE.format(sn, TOKEN_INFO_URL.format(sn)))
        file = read_txt(DOWNLOAD_TOKEN_INFO_URL.format(sn))
        # clear_token_info_txt(DOWNLOAD_TOKEN_INFO_URL.format(sn))
        acls_dict = check_and_get(file)
        acl_whitelist = read_json(PATH + 'acl_whitelist.json')
        whitelist = get_acl_dict(acl_whitelist)
        whitelist_check(whitelist, acls_dict)
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag, e.msg)
        set_log_content(LogLevel(1).name, log_tag,
                        '-------------------------- ACL check failed --------------------------')
    finally:
        set_log_content(LogLevel(2).name, log_tag,
                        '-------------------------- ACL check end --------------------------')


if __name__ == '__main__':
    sn = sys.argv[1]
    main(sn)
