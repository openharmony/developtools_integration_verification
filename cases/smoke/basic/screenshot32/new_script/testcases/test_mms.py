import logging
import os.path
import time

import pytest
from utils.images import compare_image_similarity, crop_picture


class Test:
    ability_name = 'com.ohos.mms.MainAbility'
    bundle_name = 'com.ohos.mms'

    @pytest.mark.parametrize('setup_teardown', [bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('启动信息应用')
        device.start_ability(self.bundle_name, self.ability_name)

        logging.info('信息界面截图对比')
        standard_pic = os.path.join(device.resource_path, 'mms.jpeg')
        mms_page_pic = device.save_snapshot_to_local('{}_mms.jpeg'.format(device.sn))
        crop_picture(mms_page_pic)
        similarity = compare_image_similarity(mms_page_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        # logging.info('信息界面控件检查')
        # device.refresh_layout()
        # device.assert_text_exist('信息')
