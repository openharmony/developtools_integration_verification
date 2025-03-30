import logging
import os.path
import time

import pytest

from utils.images import compare_image_similarity, crop_picture


@pytest.fixture(autouse=True)
def uninstall_hap(device):
    yield
    try:
        device.uninstall_hap('com.example.helloworld')
    except:
        pass


class Test:
    ability_name = 'EntryAbility'
    bundle_name = 'com.example.helloworld'

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('install hap')
        hap_path = os.path.join(device.resource_path, 'entry-default-signed.hap')
        device.install_hap(hap_path)
        time.sleep(1)
        logging.info('start app')
        device.start_ability(self.bundle_name, self.ability_name)
        time.sleep(2)
        main_page = device.save_snapshot_to_local('{}_hap.jpeg'.format(device.sn))
        crop_picture(picture=main_page, x1=0, y1=72, x2=160, y2=162)
        stand_pic = os.path.join(device.resource_path, 'hap.jpeg')

        similarity = compare_image_similarity(main_page, stand_pic)
        assert similarity > 0.8, '截图对比失败'
