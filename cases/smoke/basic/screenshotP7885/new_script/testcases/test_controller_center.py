import logging
import os.path
import time

import pytest
from utils.images import compare_image_similarity, crop_picture


class Test:

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('pull down controller center')
        start_x = int(device.width * 0.9)
        start_y = int(device.height * 0.01)
        end_x = start_x
        end_y = int(device.height * 0.15)
        device.swipe(from_x=start_x, from_y=start_y, to_x=end_x, to_y=end_y)
        time.sleep(2)

        logging.info('compare image similarity')
        standard_pic = os.path.join(device.resource_path, 'controller_center.jpeg')
        controller_page_pic = device.save_snapshot_to_local('{}_controller_center.jpeg'.format(device.sn))

        similarity = compare_image_similarity(controller_page_pic, standard_pic)
        device.dirc_fling(3)
        assert similarity > 0.5, 'compare similarity failed'
