import logging
import os.path
import time

import pytest
from utils.images import compare_image_similarity, crop_picture


class Test:
    ability_name = 'com.ohos.contacts.MainAbility'
    bundle_name = 'com.ohos.contacts'

    @pytest.mark.parametrize('setup_teardown', [bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('启动联系人应用')
        device.start_ability(self.bundle_name, self.ability_name)

        logging.info('联系人界面截图对比')
        standard_pic = os.path.join(device.resource_path, 'contacts.jpeg')
        contacts_page_pic = device.save_snapshot_to_local('contacts.jpeg')
        crop_picture(contacts_page_pic)
        similarity = compare_image_similarity(contacts_page_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        logging.info('联系人界面控件检查')
        device.refresh_layout()
        device.assert_text_exist('电话')
        device.assert_text_exist('联系人')
        device.assert_text_exist('收藏')
        device.assert_text_exist('1')
        device.assert_text_exist('3')
        device.assert_text_exist('5')
        device.assert_text_exist('7')
        device.assert_text_exist('9')
