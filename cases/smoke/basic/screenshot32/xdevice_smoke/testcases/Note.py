# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts

from test_case import ITestCase


class Note(ITestCase):
    ability_name = 'MainAbility'
    bundle_name = 'com.ohos.note'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('预置条件：Note测试开始，启动app')
        super().setup()
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)

    def process(self):
        self.common_oh.wait(self.Phone1, 5)
        for i in range(2):
            self.step('步骤1：第 {} 次点击允许'.format(i))
            self.common_oh.click(self.Phone1, 530, 1100, mode='NORMAL')
            self.common_oh.wait(self.Phone1, 2)
        self.step('步骤2：点击数学公式')
        self.common_oh.touchByText(self.Phone1, '数学公式', mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤3：点击屏幕弹出输入法')
        self.common_oh.click(self.Phone1, 360, 280, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 3)
        # 控件检查
        self.step('步骤4：控件检查')
        self.common_oh.checkIfTextExist(self.Phone1, '数学公式')
        self.common_oh.checkIfTextExist(self.Phone1, '未分类')
        self.common_oh.checkIfTextExist(self.Phone1, 'resource:/RAWFILE/editor.html')
        self.common_oh.checkIfTextExist(self.Phone1, 'space')
        self.step('步骤5：截图对比')
        # 截图对比
        note_pic = 'note.jpeg'
        self.take_picture_to_local(note_pic)
        self.crop_picture(note_pic)
        similarity = self.compare_image_similarity(note_pic)[0]
        self.step('{}和标准图的相似度为{}%'.format(note_pic, similarity))
        Asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.step('收尾：Note test finish')
        self.step('收尾1：点击home键')
        self.common_oh.click(self.Phone1, 515, 1240, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('收尾2：清理最近的任务')
        self.common_oh.click(self.Phone1, 360, 1170, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 5)
        super().teardown()
