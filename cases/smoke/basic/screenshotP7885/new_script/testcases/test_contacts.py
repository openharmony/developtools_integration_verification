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
        logging.info('start contacts app')
        device.start_ability(self.bundle_name, self.ability_name)
        time.sleep(5)

        # 权限允许弹窗
        device.refresh_layout()
        confirm_element = device.get_element_by_text('允许')
        if confirm_element:
            device.click_element(confirm_element)
        time.sleep(2)
        
        logging.info('compare image similarity')
        standard_pic = os.path.join(device.resource_path, 'contacts.jpeg')
        contacts_page_pic = device.save_snapshot_to_local('{}_contacts.jpeg'.format(device.sn))
        similarity = compare_image_similarity(contacts_page_pic, standard_pic)
        assert similarity > 0.5, 'compare similarity failed'
