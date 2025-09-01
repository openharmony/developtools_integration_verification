import logging
import os.path
import time

import pytest

from utils.images import compare_image_similarity, crop_picture


@pytest.fixture(autouse=True)
def uninstall_hap(device):
    yield
    try:
        device.uninstall_hap('com.samples.ArkUIInteropSample')
    except:
        pass


class Test:
    ability_name = 'EntryAbility'
    bundle_name = 'com.samples.ArkUIInteropSample'

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('install hap')
        hap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(device.resource_path))), 'ArkUIInteropSample','entry-default-signed.hap')
        device.install_hap(hap_path)
        time.sleep(5)
        logging.info('start app')
        device.start_ability(self.bundle_name, self.ability_name)
        time.sleep(2)
        main_page = device.save_snapshot_to_local('{}_hap.jpeg'.format(device.sn))
        crop_picture(picture=main_page, x1=0, y1=50, x2=700, y2=1150)
        stand_pic = os.path.join(device.resource_path, 'ui_hap.jpeg')

        similarity = compare_image_similarity(main_page, stand_pic)
        assert similarity > 0.8, '截图对比失败'
