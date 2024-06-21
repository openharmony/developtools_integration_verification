import json
import logging
import math
import os.path
import sqlite3

import pytest


class TestAPLCheck:

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        return 
        check_list_file = os.path.join(device.resource_path, 'apl_check_list.json')
        logging.info('从{}文件获取预置的check list'.format(check_list_file))
        json_data = json.load(open(check_list_file, 'r'))
        whitelist_dict = {}
        for data in json_data:
            whitelist_dict.update({data.get('bundle&processName'): int(data.get('apl'))})
        assert whitelist_dict, 'check list为空'

        logging.info('导出access_token.db')
        device.hdc_file_recv('/data/service/el1/public/access_token/access_token.db')
        db_file = os.path.join(device.report_path, 'access_token.db')
        assert os.path.exists(db_file), '{}不存在'.format(db_file)

        logging.info('查询hap_token_info_table')
        hap_apl_result = self.query_records(db_file, 'select bundle_name,apl from hap_token_info_table')
        assert hap_apl_result, 'hap_token_info_table为空'
        logging.info('查询native_token_info_table')
        native_apl_result = self.query_records(db_file, 'select process_name,apl from native_token_info_table')
        assert native_apl_result, 'native_token_info_table为空'

        logging.info('hap apl检查')
        hap_check_rst = self.compare_db_with_whitelist(hap_apl_result, whitelist_dict, 1)
        logging.info('native apl检查')
        native_check_rst = self.compare_db_with_whitelist(native_apl_result, whitelist_dict, 2)
        assert hap_check_rst, 'hap apl检查失败'
        assert native_check_rst, 'native apl检查失败'

    @staticmethod
    def query_records(db_file, sql):
        conn = sqlite3.connect(db_file)
        assert conn, 'sqlit数据库连接失败'
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        if not results:
            return
        result_dict = {}
        for line in results:
            key = line[0]
            value = 0 if math.isnan(line[1]) else line[1]
            result_dict.update({key: value})
        return result_dict

    @staticmethod
    def compare_db_with_whitelist(db_data: dict, whitelist_dict: dict, basic_value):
        """
        数据库和白名单对比
        :param db_data:
        :param whitelist_dict:
        :param basic_value:
        :return:
        """
        check_rst = True
        for key, apl in db_data.items():
            if key not in whitelist_dict.keys():
                continue
            if apl <= basic_value:
                continue
            is_pass = whitelist_dict[key] == apl
            if not is_pass:
                logging.error('bundleName/processName = {} apl = {} | 校验未通过'.format(key, apl))
                check_rst = False
            else:
                logging.info('bundleName/processName = {} apl = {} | 校验通过'.format(key, apl))
        return check_rst
