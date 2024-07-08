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

        logging.info('点击数据公式')
        device.refresh_layout()

        article = device.get_element_by_text('数学公式')
        device.click_element(article)
        time.sleep(0.5)
        logging.info('点击笔记内容区域')
        device.click(360, 300)
        time.sleep(3)
        standard_pic = os.path.join(device.resource_path, 'note.jpeg')
        note_pic = device.save_snapshot_to_local('note.jpeg')
        crop_picture(note_pic)
        similarity = compare_image_similarity(note_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        logging.info('导出笔记界面布局')
        device.refresh_layout()
        logging.info('控件检查')
        device.assert_text_exist('好好学习，天天向上')
        device.assert_text_exist('space')
