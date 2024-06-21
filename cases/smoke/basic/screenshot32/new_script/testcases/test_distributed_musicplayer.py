import logging
import os.path
import time

import pytest

from utils.images import compare_image_similarity, crop_picture


class TestDistributedMusicplayer:
    ability_name = 'ohos.samples.distributedmusicplayer.MainAbility'
    bundle_name = 'ohos.samples.distributedmusicplayer'

    @pytest.mark.parametrize('setup_teardown', [bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('启动音乐应用')
        device.start_ability(self.bundle_name, self.ability_name)
        time.sleep(2)
        # 弹窗
        device.stop_permission()
        logging.info('音乐界面截图对比')
        standard_pic = os.path.join(device.resource_path, 'distributedmusicplayer.jpeg')
        music_page_pic = device.save_snapshot_to_local('distributedmusicplayer.jpeg')
        crop_picture(music_page_pic)
        similarity = compare_image_similarity(music_page_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        logging.info('音乐界面控件检查')
        current_layout = device.generate_layout_object('music.json')
        current_layout.assert_key_exist('image1')
        current_layout.assert_key_exist('image2')
        current_layout.assert_key_exist('image3')
        current_layout.assert_key_exist('image4')
