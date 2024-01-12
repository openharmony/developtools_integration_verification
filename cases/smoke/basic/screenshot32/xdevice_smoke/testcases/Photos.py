# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts

from test_case import ITestCase


class Photos(ITestCase):
    photo_ability_name = 'com.ohos.photos.MainAbility'
    photo_bundle_name = 'com.ohos.photos'
    shot_ability_name = 'com.ohos.screenshot.ServiceExtAbility'
    shot_bundle_name = 'com.ohos.screenshot'

    def __init__(self, controllers):
        super().__init__(controllers)
        # self.tests = [
        #     'pull_down_notification_bar',
        #     'screenshot_x_y',
        #     'start_photos',
        #     'last_photos_x_y',
        #     'shot_and_compare',
        #     'process_and_sandbox_path_check',
        # ]
        
    def setup(self):
        super().setup()
        self.step('预置条件：准备Photos测试')

    def process(self):
        self.step('步骤1：下拉控制中心')
        self.common_oh.swipe(self.Phone1, x1=500, y1=0, x2=500, y2=80)
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤2：点击截屏快捷方式')
        self.common_oh.click(self.Phone1, 115, 480, 'NORMAL')
        self.common_oh.wait(self.Phone1, 5)
        self.step('步骤3：启动相册app')
        self.common_oh.startAbility(self.Phone1, self.photo_ability_name, self.photo_bundle_name)
        self.common_oh.wait(self.Phone1, 5)
        self.step('步骤4：点击最近')
        self.common_oh.click(self.Phone1, 100, 220, 'NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        # 控件检查
        self.step('步骤5：控件检查')
        self.common_oh.checkIfKeyExist(self.Phone1, 'ActionBarButtonBack')
        self.common_oh.checkIfKeyExist(self.Phone1, 'ToolBarButtonFavor')
        self.common_oh.checkIfKeyExist(self.Phone1, 'ToolBarButtonDelete')
        self.common_oh.checkIfTextExist(self.Phone1, '收藏')
        self.common_oh.checkIfTextExist(self.Phone1, '删除')
        # 截图对比
        self.step('步骤6：截图对比')
        photos_pic = 'photos.jpeg'
        self.take_picture_to_local(photos_pic)
        self.crop_picture(photos_pic)
        similarity = self.compare_image_similarity(photos_pic)[0]
        self.step('{}和标准图的相似度为{}%'.format(photos_pic, similarity))
        Asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)
        self.step('步骤7：medialibrarydata进程检查')
        process = 'com.ohos.medialibrary.medialibrarydata'
        Asserts.assert_true(self.common_oh.isProcessRunning(self.Phone1, process))
        self.common_oh.wait(self.Phone1, 1)
        # sandbox path检查
        self.step('步骤7：检查sandbox path')
        pid_num = self.common_oh.shell(self.Phone1, 'pgrep -f {}'.format(process)).strip()
        self.common_oh.wait(self.Phone1, 1)
        sanboxf = self.common_oh.shell(self.Phone1, 'echo \"ls /storage/media/local/\"|nsenter -t {} -m sh'.format(pid_num))
        self.common_oh.wait(self.Phone1, 1)
        Asserts.assert_in('files', sanboxf)

    def teardown(self):
        self.step('stop photo app')
        self.common_oh.forceStopAbility(self.Phone1, self.photo_bundle_name)
        # self.collect_hilog('Photos.tar')
        self.step('photo test finish')
        super().teardown()