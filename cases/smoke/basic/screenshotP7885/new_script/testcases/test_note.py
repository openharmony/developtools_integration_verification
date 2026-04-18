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
        # 截取笔记主页面
        device.save_snapshot_to_local('{}_note_mainpage.jpeg'.format(device.sn))

        # 点击数学公式
        logging.info('click shuxue gongshi')
        device.refresh_layout()
        math_formula_element = device.get_element_by_text('数学公式')
        assert math_formula_element, '数学公式 component not found'
        device.click_element(math_formula_element)

        time.sleep(4)
        logging.info('click note content area')
        device.refresh_layout()
        for i in range(5):
            device.click(360, 325)
            time.sleep(2)
            device.click(360, 324)
            time.sleep(3)
            if device.is_soft_keyboard_on():
                break
        time.sleep(3)
        standard_pic = os.path.join(device.resource_path, 'note.jpeg')
        note_pic = device.save_snapshot_to_local('{}_note.jpeg'.format(device.sn))
        logging.info('compare image similarity')
        similarity = compare_image_similarity(note_pic, standard_pic)
        assert similarity > 0.5, 'compare similarity failed'
