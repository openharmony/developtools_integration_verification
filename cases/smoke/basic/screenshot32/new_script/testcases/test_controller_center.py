import logging
import os.path
import time

import pytest
from utils.images import compare_image_similarity, crop_picture


class Test:

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('pull down controller center')
        device.swipe(from_x=500, from_y=1, to_x=500, to_y=120)
        time.sleep(2)

        logging.info('compare image similarity')
        standard_pic = os.path.join(device.resource_path, 'controller_center.jpeg')
        controller_page_pic = device.save_snapshot_to_local('{}_controller_center.jpeg'.format(device.sn))

        crop_picture(controller_page_pic)
        similarity = compare_image_similarity(controller_page_pic, standard_pic)
        device.dirc_fling(3)
        assert similarity > 0.5, 'compare similarity failed'
