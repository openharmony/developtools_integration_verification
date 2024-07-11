import logging
import os.path
import time

import pytest
from utils.images import compare_image_similarity, crop_picture


class Test:
    ability_name = 'ohos.samples.distributedmusicplayer.MainAbility'
    bundle_name = 'ohos.samples.distributedmusicplayer'

    @pytest.mark.parametrize('setup_teardown', [bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('start music app')
        device.start_ability(self.bundle_name, self.ability_name)
        # 弹窗
        device.stop_permission()
        logging.info('compare image similarity')
        standard_pic = os.path.join(device.resource_path, 'distributedmusicplayer.jpeg')
        music_page_pic = device.save_snapshot_to_local('{}_distributedmusicplayer.jpeg'.format(device.sn))
        crop_picture(music_page_pic)
        similarity = compare_image_similarity(music_page_pic, standard_pic)
        assert similarity > 0.5, 'compare similarity failed'

        # logging.info('音乐界面控件检查')
        # device.refresh_layout()
        # device.assert_key_exist('image1')
        # device.assert_key_exist('image2')
        # device.assert_key_exist('image3')
        # device.assert_key_exist('image4')
