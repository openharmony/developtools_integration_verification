import json
import os
import time
import logging
import pytest
import sqlite3


class Test:
    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        t = time.time()

        check_list_file = os.path.join(device.resource_path, 'acl_whitelist.json')
        assert os.path.exists(check_list_file), '{} not exist'.format(check_list_file)
        logging.info('reading {} content'.format(check_list_file))
        whitelist_dict = {}
        json_data = json.load(open(check_list_file, 'r'))
        for item in json_data:
            whitelist_dict.update({item.get('processName'): item.get('acls')})

        logging.info('exporting access_token.db')
        device.hdc_file_recv('/data/service/el1/public/access_token/access_token.db')
        device.hdc_file_recv('/data/service/el1/public/access_token/access_token.db-wal')
        device.hdc_file_recv('/data/service/el1/public/access_token/access_token.db-shm')
        db_file = os.path.join(device.report_path, 'access_token.db')
        assert os.path.exists(db_file), '{} not exist'.format(db_file)

        logging.info('exporting permission_definitions.json')
        DEFINE_PERMISSION_FILE = "/system/etc/access_token/permission_definitions.json"
        device.hdc_file_recv(DEFINE_PERMISSION_FILE)
        perm_def_file = os.path.join(device.report_path, 'permission_definitions.json')
        assert os.path.exists(perm_def_file), '{} not exist'.format(perm_def_file)

        logging.info('exporting nativetoken.json')
        SA_INFO_FILE = "/data/service/el0/access_token/nativetoken.json"
        device.hdc_file_recv(SA_INFO_FILE)
        sa_info_file = os.path.join(device.report_path, 'nativetoken.json')
        assert os.path.exists(sa_info_file), '{} not exist'.format(sa_info_file)

        logging.info('insert permission_definition_table')
        self.insert_perm(perm_def_file, db_file)

        logging.info('querying native_token_info_table')

        sa_result = self.query_sa_info(db_file, sa_info_file)
        assert sa_result, 'native_token_info_table is empty'
        
        logging.info('querying from native_token_info_table end')

        check_rst = True
        for process, permission_list in sa_result.items():
            if process not in whitelist_dict.keys():
                check_rst = False
                logging.error('processName={} not configured while list permission: {}'.format(process, permission_list))
            else:
                whitelist_set = set(whitelist_dict[process])
                permission_set = set(permission_list)
                not_applied = permission_set.difference(whitelist_set)
                if not_applied:
                    check_rst = False
                    logging.error('processName={} not configured while list permission: {}'.format(process, not_applied))

        logging.info("ACL CHECK COST: {}s".format(time.time() - t))
        assert check_rst, 'ACL check failed'

    @staticmethod
    def query_sa_info(db_file, sa_info_file):
        sql = 'SELECT permission_name, available_level FROM permission_definition_table;'
        conn = sqlite3.connect(db_file)
        assert conn, 'sqlit database connect failed'
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        
        perm_map ={}
        for item in results:
            permission_name = item[0]
            apl = item[1]
            perm_map[permission_name] = apl

        check_pass = True
        result_map ={}

        with open(sa_info_file, 'r') as file:
            data = json.load(file)
            for item in data:
                processName = item.get('processName')
                APL = item.get('APL')
                if APL == 3:
                    logging.info('{} APL = 3, PASS.'.format(processName))
                    continue

                permissions = item.get('permissions')

                if not permissions:
                    logging.info('Process {} does not apply for permission, PASS.'.format(processName))
                    continue

                nativeAcls = item.get('nativeAcls')
                for perm in permissions:
                    if perm in nativeAcls:
                        continue
                    
                    PAPL = perm_map.get(perm)
                    if not PAPL:
                        logging.warning('{} no definition'.format(perm))
                        continue
                    if PAPL > APL:
                        logging.error('{} invalid is detected in {}'.format(perm, processName))
                        check_pass = False
                
                if nativeAcls:
                    result_map[processName] = nativeAcls
        
        assert check_pass, 'ACL check failed'
        return result_map

    @staticmethod
    def insert_perm(perm_def_file, db_file):
        query_perm_sql = "select permission_name from permission_definition_table;"
        conn = sqlite3.connect(db_file)
        assert conn, 'sqlit database connect failed'
        cursor = conn.cursor()
        cursor.execute(query_perm_sql)
        perms_list = cursor.fetchall()
        conn.close()
        perms_set = set()
        for perms in perms_list:
            perms_set.add(perms[0])

        sql = 'insert into permission_definition_table(token_id, permission_name, bundle_name, grant_mode, available_level, provision_enable, distributed_scene_enable, label, label_id, description, description_id, available_type) values(560, ?, "xxxx", 1, ?, 1, 1, "xxxx", 1, "xxxx", 1, 1)'
        sql_data = []
        with open(perm_def_file, 'r') as file:
            data = json.load(file)
            system_grant_list = data.get('systemGrantPermissions')
            user_grant_list = data.get('userGrantPermissions')
            for item in user_grant_list:
                key = item.get('name')
                if key not in perms_set:
                    value_str = item.get('availableLevel')
                    value = 1
                    if value_str == "system_core":
                        value = 3
                    elif value_str == "system_basic":
                        value = 2
                    sql_data.append([key, value])
            for item in system_grant_list:
                key = item.get('name')
                if key not in perms_set:
                    value_str = item.get('availableLevel')
                    value = 1
                    if value_str == "system_core":
                        value = 3
                    elif value_str == "system_basic":
                        value = 2
                    sql_data.append([key, value])
    
        logging.warning('insert permission_definition_table size: {}'.format(len(sql_data)))
        conn = sqlite3.connect(db_file)
        assert conn, 'sqlit database connect failed'
        cursor = conn.cursor()
        cursor.executemany(sql, sql_data)
        results = cursor.fetchall()
        conn.commit()
        conn.close()
        