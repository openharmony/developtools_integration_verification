# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts
from devicetest.log.logger import print_info

from test_case import ITestCase


class Photos(ITestCase):
    photo_ability_name = 'com.ohos.photos.MainAbility'
    photo_bundle_name = 'com.ohos.photos'
    shot_ability_name = 'com.ohos.screenshot.ServiceExtAbility'
    shot_bundle_name = 'com.ohos.screenshot'

    def __init__(self, controllers):
        super().__init__(controllers)
        
    def setup(self):
        self.step('前置条件1：回到桌面')
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')

    def process(self):
        self.step('步骤1：启动相册app')
        self.common_oh.startAbility(self.Phone1, self.photo_ability_name, self.photo_bundle_name)
        # 控件检查
        self.step('步骤2：控件检查')
        self.common_oh.checkIfTextExist(self.Phone1, '照片')
        self.common_oh.checkIfTextExist(self.Phone1, '相册')
        # 截图对比
        self.step('步骤3：截图对比')
        photos_pic = 'photos.jpeg'
        self.take_picture_to_local(photos_pic)
        self.crop_picture(photos_pic)
        similarity = self.compare_image_similarity(photos_pic)
        print_info('相似度为：{}%'.format(similarity))
        self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)
        self.step('步骤4：medialibrarydata进程检查')
        process = 'com.ohos.medialibrary.medialibrarydata'
        self.common_oh.isProcessRunning(self.Phone1, process)
        self.common_oh.wait(self.Phone1, 1)
        # sandbox path检查
        self.step('步骤5：检查sandbox path')
        pid_num = self.common_oh.shell(self.Phone1, 'pgrep -f {}'.format(process)).strip()
        self.common_oh.wait(self.Phone1, 1)
        sanboxf = self.common_oh.shell(self.Phone1, 'echo \"ls /storage/media/local/\"|nsenter -t {} -m sh'.format(pid_num))
        self.common_oh.wait(self.Phone1, 1)
        self.asserts.assert_in('files', sanboxf)

    def teardown(self):
        self.step('收尾1：停掉相册应用')
        self.common_oh.forceStopAbility(self.Phone1, self.photo_bundle_name)
