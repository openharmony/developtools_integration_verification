import logging
import time

import pytest


class Test:
    camera_ability_name = 'com.ohos.camera.MainAbility'
    camera_bundle_name = 'com.ohos.camera'
    photo_ability_name = 'com.ohos.photos.MainAbility'
    photo_bundle_name = 'com.ohos.photos'

    @pytest.mark.parametrize('setup_teardown', [camera_bundle_name], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('启动相机应用')
        device.start_ability(self.camera_bundle_name, self.camera_ability_name)
        time.sleep(2)
        device.save_snapshot_to_local('step1.jpeg')

        logging.info('点击拍照')
        device.click(360, 1095)
        time.sleep(2)
        device.save_snapshot_to_local('step2.jpeg')

        logging.info('切到录像模式')
        device.click(430, 980)
        time.sleep(2)
        device.save_snapshot_to_local('step3.jpeg')

        logging.info('点击录制')
        device.click(360, 1095)
        time.sleep(5)
        device.save_snapshot_to_local('step4.jpeg')

        logging.info('停止录制')
        device.click(320, 1095)
        time.sleep(2)
        device.save_snapshot_to_local('step5.jpeg')

        logging.info('点击左下角切到相册')
        device.click(200, 1095)
        time.sleep(5)
        device.save_snapshot_to_local('step6.jpeg')

        device.assert_process_running(self.photo_bundle_name)
