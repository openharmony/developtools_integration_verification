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

        logging.info('设置界面截图对比')
        standard_pic = os.path.join(device.resource_path, 'settings.jpeg')
        settings_page_pic = device.save_snapshot_to_local('{}_settings.jpeg'.format(device.sn))
        crop_picture(settings_page_pic)
        similarity = compare_image_similarity(settings_page_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        # logging.info('设置界面控件检查')
        # device.refresh_layout()
        # device.assert_text_exist('设置')
        # device.assert_text_exist('WLAN')

        logging.info('进入wlan页面')
        # wlan_element = device.get_element_by_text('WLAN')
        # device.click_element(wlan_element)
        device.click(160, 306)
        time.sleep(1)
        # device.refresh_layout()
        # wlan_switch = device.get_element_by_type('Toggle')
        before_click = device.get_wifi_status().get('active')

        logging.info('打开/关闭 wlan开关')
        # device.click_element(wlan_switch)
        device.click(646, 210)
        time.sleep(5)
        after_click = device.get_wifi_status().get('active')
        logging.info('wlan开关状态变化：{} => {}'.format(before_click, after_click))
        assert before_click != after_click, 'wlan开关切换失败'
