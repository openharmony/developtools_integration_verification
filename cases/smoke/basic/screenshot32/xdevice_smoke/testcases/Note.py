# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts
from devicetest.log.logger import print_info

from test_case import ITestCase


class Note(ITestCase):
    ability_name = 'MainAbility'
    bundle_name = 'com.ohos.note'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：回到桌面')
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')
        self.step('预置条件：Note测试开始，启动app')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)

    def process(self):
        self.step('步骤1：启动备忘录')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)
        # self.common_oh.wait(self.Phone1, 5)
        for i in range(2):
            self.step('步骤2：第 {} 次点击允许'.format(i))
            self.common_oh.click(self.Phone1, 530, 1100, mode='NORMAL')
            self.common_oh.wait(self.Phone1, 2)
        self.step('步骤3：点击数学公式')
        self.common_oh.touchByText(self.Phone1, '数学公式', mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤4：点击屏幕弹出输入法')
        self.common_oh.click(self.Phone1, 360, 280, mode='NORMAL')
        self.common_oh.click(self.Phone1, 360, 280, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 5)
        # 控件检查
        self.step('步骤5：控件检查')
        self.common_oh.checkIfTextExist(self.Phone1, '好好学习', pattern='CONTAINS')
        self.step('步骤6：截图对比')
        # 截图对比
        note_pic = 'note.jpeg'
        self.take_picture_to_local(note_pic)
        self.crop_picture(note_pic)
        similarity = self.compare_image_similarity(note_pic)
        print_info('相似度为：{}%'.format(similarity))
        self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.step('收尾1：点击home键')
        self.common_oh.click(self.Phone1, 515, 1240, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('收尾2：清理最近的任务')
        self.common_oh.click(self.Phone1, 360, 1170, mode='NORMAL')
        # self.common_oh.wait(self.Phone1, 5)
