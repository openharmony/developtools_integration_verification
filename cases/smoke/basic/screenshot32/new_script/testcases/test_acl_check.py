import json
import os
import time
import logging
import pytest


class Test:
    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        return
        check_list_file = os.path.join(device.resource_path, 'acl_whitelist.json')
        assert os.path.exists(check_list_file), '{} not exist'.format(check_list_file)
        logging.info('reading {} content'.format(check_list_file))
        whitelist_dict = {}
        json_data = json.load(open(check_list_file, 'r'))
        for item in json_data:
            whitelist_dict.update({item.get('processName'): item.get('acls')})

        logging.info('exporting token_info')
        token_file = 'token_info_{}.txt'.format(time.time_ns())
        device.hdc_shell('atm dump -t > /data/{}'.format(token_file))
        device.hdc_file_recv('/data/{}'.format(token_file))
        local_file = os.path.join(device.report_path, token_file)
        assert os.path.exists(local_file), 'token_info export failed'
        device.hdc_shell('rm -rf /data/{}'.format(token_file))
        acls_in_device = self.check_and_get_native_acls(local_file)

        check_rst = True
        for process, permission_list in acls_in_device.items():
            if process not in whitelist_dict.keys():
                check_rst = False
                logging.info('processName={} not configured while list permission: {}'.format(process, permission_list))
            else:
                whitelist_set = set(whitelist_dict[process])
                permission_set = set(permission_list)
                not_applied = permission_set.difference(whitelist_set)
                if not_applied:
                    check_rst = False
                    logging.info('processName={}not configured while list permission: {}'.format(process, not_applied))
        assert check_rst, 'ACL check failed'

    @staticmethod
    def check_and_get_native_acls(token_file):
        check_pass = True
        with open(token_file, 'r') as f:
            lines = f.readlines()
        native_acls_dict = {}
        process = ''
        for line in lines:
            if 'processName' in line:
                process = line.split(':')[1].strip().strip('",')
            elif 'invalidPermList' in line:
                check_pass = False
                logging.info('invalidPermList is detected in processName = {}'.format(process))
            elif 'nativeAcls' in line:
                permissions = line.split(':')[1].strip().strip('",')
                if not permissions:
                    continue
                native_acls_dict.update(
                    {
                        process: permissions.split(',')
                    }
                )
        assert check_pass, 'ACL check failed'
        return native_acls_dict
