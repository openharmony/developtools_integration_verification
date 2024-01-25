# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts
from devicetest.log.logger import print_info

from test_case import ITestCase


class DistributedMusicPlayer(ITestCase):
    ability_name = 'ohos.samples.distributedmusicplayer.MainAbility'
    bundle_name = 'ohos.samples.distributedmusicplayer'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：回到桌面')
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')


    def process(self):
        self.step('步骤1：启动音乐应用')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)
        # self.common_oh.wait(self.Phone1, 5)
        self.step('步骤2：点击弹窗的"允许"')
        try:
            self.common_oh.touchByText(self.Phone1, '允许')
        except:
            pass

        self.step('步骤3：检查是否进入音乐')
        # 控件检查
        self.common_oh.checkIfKeyExist(self.Phone1, 'image1')
        self.common_oh.checkIfKeyExist(self.Phone1, 'image3')

        self.step('步骤4：截图对比')
        pic_name = 'distributedmusicplayer.jpeg'
        self.take_picture_to_local(pic_name)
        self.crop_picture(pic_name)
        similarity = self.compare_image_similarity(pic_name)
        print_info('相似度为：{}%'.format(similarity))
        # 控件对比和截图对比有一个成功就认为pass
        self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.step('收尾1：停掉音乐应用')
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
        self.common_oh.cleanApplicationData(self.Phone1, self.bundle_name)