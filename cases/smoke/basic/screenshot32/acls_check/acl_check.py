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


def main():
    set_log_content(LogLevel(2).name, log_tag,
                    '-------------------------- ACL check begin --------------------------')
    try:
        hdc_command(GENERATING_TOKEN_INFO_COMMAND)
        hdc_command(DOWNLOAD_TOKEN_INFO_COMMAND)
        hdc_command(CLEAR_TOKEN_INFO_FILE)
        file = read_txt(DOWNLOAD_TOKEN_INFO_URL)
        clear_token_info_txt(DOWNLOAD_TOKEN_INFO_URL)
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
    main()
