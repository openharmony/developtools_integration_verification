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
        logging.info('sart camera app')
        device.start_ability(self.camera_bundle_name, self.camera_ability_name)
        device.save_snapshot_to_local('{}_camera_step1.jpeg'.format(device.sn))

        logging.info('click shot button')
        device.click(360, 1095)
        time.sleep(2)
        device.save_snapshot_to_local('{}_camera_step2.jpeg'.format(device.sn))

        logging.info('switch to record mode')
        device.click(430, 980)
        time.sleep(2)
        device.save_snapshot_to_local('{}_camera_step3.jpeg'.format(device.sn))

        logging.info('click shot button')
        device.click(360, 1095)
        time.sleep(5)
        device.save_snapshot_to_local('{}_camera_step4.jpeg'.format(device.sn))

        logging.info('stop recoding')
        device.hdc_shell(f'uitest uiInput click 320 1095')
        time.sleep(3)
        device.save_snapshot_to_local('{}_camera_step5.jpeg'.format(device.sn))

        logging.info('click left behind button in order to switch to gallery app')
        device.click(200, 1095)
        time.sleep(5)
        device.save_snapshot_to_local('{}_camera_step6.jpeg'.format(device.sn))
        #device.assert_process_running(self.photo_bundle_name)
