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

        logging.info('insert permission_definition_table')
        self.insert_perm(perm_def_file, db_file)

        logging.info('querying native_token_info_table')

        sa_result = self.query_sa_info(db_file)
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
    def query_sa_info(db_file):
        sql = """
        SELECT t3.token_id token_id,
            t3.process_name process_name,
            t3.apl SAPL,
            t3.native_acls native_acls,
            tp.PAPL PAPL,
            tp.permission_name permission_name
        FROM native_token_info_table t3
            LEFT JOIN ( 
            SELECT t1.token_id token_id,
                t1.permission_name permission_name,
                t2.available_level PAPL
            FROM permission_state_table AS t1
                LEFT JOIN permission_definition_table AS t2
                        ON t1.permission_name = t2.permission_name 
        ) 
        AS tp
                    ON t3.token_id = tp.token_id
        WHERE permission_name IS NOT NULL 
            AND
            t3.apl < tp.PAPL;
        """
        conn = sqlite3.connect(db_file)
        assert conn, 'sqlit database connect failed'
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        
        result_map ={}
        if not results:
            return result_map

        check_pass = True

        for item in results:
            process_name = item[1]
            SAPL = item[2]
            
            permission_name = item[5]
            
            native_acls = item[3]
            if native_acls.strip() == "":
                logging.error('{} invalid is detected in {}'.format(permission_name, process_name))
                check_pass = False
                continue
            else:
                native_acl_list = native_acls.split(',')
                if permission_name not in native_acl_list:
                    logging.error('{} invalid is detected in {}'.format(permission_name, process_name))
                    check_pass = False
                    continue
                        
            if process_name in result_map:
                result_map.get(process_name).append(permission_name)
            else:
                result_map[process_name] = [permission_name]

        assert check_pass, 'ACL check failed'
        return result_map

    @staticmethod
    def insert_perm(perm_def_file, db_file):
        sql = 'insert into permission_definition_table(token_id, permission_name, bundle_name, grant_mode, available_level, provision_enable, distributed_scene_enable, label, label_id, description, description_id, available_type) values(560, ?, "xxxx", 1, ?, 1, 1, "xxxx", 1, "xxxx", 1, 1)'
        sql_data = []
        with open(perm_def_file, 'r') as file:
            data = json.load(file)
            system_grant_list = data.get('systemGrantPermissions')
            user_grant_list = data.get('userGrantPermissions')
            for item in user_grant_list:
                availableType = item.get('availableType')
                
                if availableType == "SERVICE":
                    key = item.get('name')
                    value_str = item.get('availableLevel')
                    value = 1
                    if value_str == "system_core":
                        value = 3
                    elif value_str == "system_basic":
                        value = 2
                    sql_data.append([key, value])
            for item in system_grant_list:
                availableType = item.get('availableType')
                
                if availableType == "SERVICE":
                    key = item.get('name')
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
        