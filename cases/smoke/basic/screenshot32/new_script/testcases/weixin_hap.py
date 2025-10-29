import logging
import os.path
import time

import pytest

from utils.images import compare_image_similarity, crop_picture


@pytest.fixture(autouse=True)
def uninstall_hap(device):
    yield
    try:
        device.uninstall_hap('com.tencenta.mm')
    except:
        pass


class Test:
    ability_name = 'EntryAbility'
    bundle_name = 'com.tencenta.mm'

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('install hap')
        hap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(device.resource_path))), 'fangweixin','entry-default-signed.hap')
        device.install_hap(hap_path)
        time.sleep(10)
        logging.info('start app')
        device.start_ability(self.bundle_name, self.ability_name)
        device.click(506,740)
        time.sleep(3)
        device.click(506,740)
        time.sleep(3)
        device.click(506,740)
        time.sleep(5)
        main_page = device.save_snapshot_to_local('{}_weixin.jpeg'.format(device.sn))
        stand_pic = os.path.join(device.resource_path, 'weixin_hap.jpeg')
        similarity = compare_image_similarity(main_page, stand_pic)
        assert similarity > 0.8, '截图对比失败'
