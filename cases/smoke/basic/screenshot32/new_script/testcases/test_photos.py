import logging
import os.path
import time

import pytest
from utils.images import compare_image_similarity, crop_picture


class Test:
    ability_name = 'com.ohos.photos.MainAbility'
    bundle_name = 'com.ohos.photos'

    @pytest.mark.parametrize('setup_teardown', [bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('启动图库应用')
        device.start_ability(self.bundle_name, self.ability_name)

        logging.info('图库界面截图对比')
        standard_pic = os.path.join(device.resource_path, 'photos.jpeg')
        photos_page_pic = device.save_snapshot_to_local('photos.jpeg')
        crop_picture(photos_page_pic)
        similarity = compare_image_similarity(photos_page_pic, standard_pic)
        assert similarity > 0.5, '截图对比失败'

        logging.info('图库界面控件检查')
        device.refresh_layout()
        device.assert_text_exist('照片')
        device.assert_text_exist('相册')

        logging.info('medialibrarydata进程检查')
        process = 'com.ohos.medialibrary.medialibrarydata'
        device.assert_process_running(process)
        time.sleep(1)

        logging.info('sandbox path检查')
        pid = device.get_pid(process)
        sanboxf = device.hdc_shell('echo "ls /storage/media/local/"|nsenter -t {} -m sh'.format(pid))
        assert 'files' in sanboxf, '{}中未检测到files'.format(sanboxf)
