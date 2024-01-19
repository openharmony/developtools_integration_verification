# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts

from test_case import ITestCase


class DistributedMusicPlayer(ITestCase):
    ability_name = 'ohos.samples.distributedmusicplayer.MainAbility'
    bundle_name = 'ohos.samples.distributedmusicplayer'

    def __init__(self, controllers):
        super().__init__(controllers)
        # self.tests = [
        #     'shot_and_compare',
        # ]

    def setup(self):
        super().setup()
        self.step('预置条件：DistributedMusicPlayer 测试开始, 启动app')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)

    def process(self):
        self.common_oh.wait(self.Phone1, 5)
        self.step('点击允许')
        self.common_oh.wait(self.Phone1, 2)
        try:
            self.common_oh.touchByText(self.Phone1, '允许')
        except:
            pass
        for i in range(3):
            self.common_oh.click(self.Phone1, 540, 1050, mode='NORMAL')
        self.step('控件检查')
        # 控件检查
        self.common_oh.checkIfTextExist(self.Phone1, 'dynamic.wav')
        self.common_oh.checkIfKeyExist(self.Phone1, 'image1')
        self.common_oh.checkIfKeyExist(self.Phone1, 'image2')
        self.common_oh.checkIfKeyExist(self.Phone1, 'image3')
        self.common_oh.checkIfKeyExist(self.Phone1, 'image4')

        self.step('截图对比')
        pic_name = 'distributedmusicplayer.jpeg'
        self.take_picture_to_local(pic_name)
        self.crop_picture(pic_name)
        similarity = self.compare_image_similarity(pic_name)[0]
        self.step('{}和标准图的相似度为{}%'.format(pic_name, similarity))
        # 控件对比和截图对比有一个成功就认为pass
        Asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
        self.common_oh.cleanApplicationData(self.Phone1, self.bundle_name)
        # self.collect_hilog('DistributedMusicPlayer.tar')
        self.step('DistributedMusicPlayer测试结束')
        super().teardown()
