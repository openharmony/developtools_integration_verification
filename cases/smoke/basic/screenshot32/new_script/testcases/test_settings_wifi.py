import logging
import os.path
import time

import pytest

from utils.images import compare_image_similarity, crop_picture


class Test:
    ability_name = 'com.ohos.settings.MainAbility'
    bundle_name = 'com.ohos.settings'

    @pytest.mark.parametrize('setup_teardown', [bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('启动设置应用')
        device.start_ability(self.bundle_name, self.ability_name)
        time.sleep(2)

        logging.info('设置界面截图对比')
        standard_pic = os.path.join(device.resource_path, 'settings.jpeg')
        settings_page_pic = device.save_snapshot_to_local('settings.jpeg')
        crop_picture(settings_page_pic)
        similarity = compare_image_similarity(settings_page_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        logging.info('设置界面控件检查')
        settings_layout = device.generate_layout_object('settings.json')
        settings_layout.assert_text_exist('设置')
        settings_layout.assert_text_exist('WLAN')

        logging.info('进入wlan页面')
        wlan_element = settings_layout.get_element_by_text('WLAN')
        device.click(*settings_layout.center_of_element(wlan_element))
        time.sleep(2)
        device.save_snapshot_to_local('wlan_snapshot1.jpeg')
        wlan_page_layout = device.generate_layout_object('wlan_before_clicked.json')
        wlan_switch = wlan_page_layout.get_element_by_type('Toggle')
        before_click = device.get_wifi_status().get('active')

        logging.info('打开/关闭 wlan开关')
        device.click(*wlan_page_layout.center_of_element(wlan_switch))
        time.sleep(5)
        device.save_snapshot_to_local('wlan_snapshot2.jpeg')
        after_click = device.get_wifi_status().get('active')
        logging.info('wlan开关状态变化：{} => {}'.format(before_click, after_click))
        assert before_click != after_click, 'wlan开关切换失败'
