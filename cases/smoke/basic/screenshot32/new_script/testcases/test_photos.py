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
        logging.info('start gallery app')
        device.start_ability(self.bundle_name, self.ability_name)

        logging.info('compare image similarity')
        standard_pic = os.path.join(device.resource_path, 'photos.jpeg')
        photos_page_pic = device.save_snapshot_to_local('{}_photos.jpeg'.format(device.sn))
        crop_picture(photos_page_pic)
        similarity = compare_image_similarity(photos_page_pic, standard_pic)
        assert similarity > 0.5, 'compare similarity failed'

        logging.info('medialibrarydata process check')
        process = 'com.ohos.medialibrary.medialibrarydata'
        device.assert_process_running(process)
        time.sleep(1)

        logging.info('sandbox path check')
        pid = device.get_pid(process)
        sanboxf = device.hdc_shell('echo \"ls /storage/media/local/\"|nsenter -t {} -m sh'.format(pid))
        assert 'files' in sanboxf, 'files not in {}'.format(sanboxf)
