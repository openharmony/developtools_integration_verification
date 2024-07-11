import logging
import os.path
import time

import pytest
from utils.images import compare_image_similarity, crop_picture


class Test:
    ability_name = 'MainAbility'
    bundle_name = 'com.ohos.note'

    @pytest.mark.parametrize('setup_teardown', [bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('start note app')
        device.start_ability(self.bundle_name, self.ability_name)

        device.save_snapshot_to_local('{}_note_mainpage.jpeg'.format(device.sn))
        logging.info('click shuxue gongshi')
        # device.refresh_layout()
        # article = device.get_element_by_text('数学公式')
        # device.click_element(article)
        device.click(464, 313)
        time.sleep(1)
        logging.info('click note content area')
        for i in range(5):
            device.click(360, 325)
            time.sleep(1)
            if device.is_soft_keyboard_on():
                break
        time.sleep(2)
        standard_pic = os.path.join(device.resource_path, 'note.jpeg')
        note_pic = device.save_snapshot_to_local('{}_note.jpeg'.format(device.sn))
        crop_picture(note_pic)
        logging.info('compare image similarity')
        similarity = compare_image_similarity(note_pic, standard_pic)
        assert similarity > 0.5, 'compare similarity failed'

        # logging.info('导出笔记界面布局')
        # device.refresh_layout()
        # logging.info('控件检查')
        # device.assert_text_exist('好好学习，天天向上')
        # device.assert_text_exist('space')
