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
        logging.info('启动备忘录应用')
        device.start_ability(self.bundle_name, self.ability_name)
        time.sleep(2)

        logging.info('主界面截图')
        device.save_snapshot_to_local('step1.jpeg')
        logging.info('导出界面布局')
        note_layout = device.generate_layout_object('note.json')
        logging.info('点击数据公式')
        article = note_layout.get_element_by_text('数学公式')
        device.click(*note_layout.center_of_element(article))
        time.sleep(2)
        device.save_snapshot_to_local('step2.jpeg')

        logging.info('点击笔记内容区域')
        device.click(360, 300)
        time.sleep(3)
        standard_pic = os.path.join(device.resource_path, 'note.jpeg')
        note_pic = device.save_snapshot_to_local('step3.jpeg')
        crop_picture(note_pic)
        similarity = compare_image_similarity(note_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        logging.info('导出笔记界面布局')
        note_layout2 = device.generate_layout_object('note_content.json')
        logging.info('控件检查')
        note_layout2.assert_text_exist('好好学习，天天向上')
        note_layout2.assert_text_exist('space')
