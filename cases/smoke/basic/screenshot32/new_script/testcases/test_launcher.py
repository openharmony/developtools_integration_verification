import logging
import os
import time

import pytest

from utils.images import compare_image_similarity


class Test:


    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('compare image similarity')
        # usb弹窗


        if device.get_focus_window() == 'SystemDialog1':
            rst = self.hdc_shell(f'ps -ef | grep -w com.ohos.systemui | grep -v grep')
            rst_list = rst.split()
            logging.info(f'Process ID: {rst_list[1]}')
            device.hdc_shell(f'kill -9 {rst_list[1]}')
            # device.click(595, 555)
            time.sleep(5)
            device.unlock()
            time.sleep(2)

        device.click(360, 1245)
        device.unlock()
        time.sleep(1)
        #if device.get_focus_window() == 'SystemDialog1':
        #    device.click(360, 800)
        #    time.sleep(10)
        standard_pic = os.path.join(device.resource_path, 'launcher.jpeg')
        launcher_pic = device.save_snapshot_to_local('{}_launcher.jpeg'.format(device.sn))
        similarity = compare_image_similarity(launcher_pic, standard_pic)
        assert similarity > 0.5, 'compare similarity failed'

        # logging.info('检查桌面图标控件是否存在')
        # device.refresh_layout()
        # device.assert_type_exist('Badge')
