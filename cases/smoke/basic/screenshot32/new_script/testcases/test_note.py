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
        device.click(464, 313)
        time.sleep(4)
        device.click(464, 313)
        time.sleep(4)
        logging.info('click note content area')
        for i in range(5):
            device.click(360, 325)
            time.sleep(2)
            device.click(360, 324)
            time.sleep(3)
            if device.is_soft_keyboard_on():
                break
        time.sleep(3)
        device.wakeup()
        device.unlock()
        time.sleep(2)
        standard_pic = os.path.join(device.resource_path, 'note.jpeg')
        note_pic = device.save_snapshot_to_local('{}_note.jpeg'.format(device.sn))
        crop_picture(note_pic)
        logging.info('compare image similarity')
        similarity = compare_image_similarity(note_pic, standard_pic)
        assert similarity > 0.5, 'compare similarity failed'
