# -*- coding: utf-8 -*-
import json
import os

from devicetest.api import Asserts
from devicetest.aw.OpenHarmony import WifiHelper
from devicetest.log.logger import print_info

from test_case import ITestCase


class SettingsWifi(ITestCase):
    app_name = 'settings_wifi'
    ability_name = 'com.ohos.settings.MainAbility'
    bundle_name = 'com.ohos.settings'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：关闭wifi，回到桌面')
        try:
            WifiHelper.closeWifi(self.Phone1)
        except:
            pass
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')

    def process(self):
        self.step('步骤1：打开设置')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)
        self.step('步骤2：检查是否在设置界面')
        self.common_oh.checkIfTextExist(self.Phone1, '设置')
        self.common_oh.checkIfTextExist(self.Phone1, 'WLAN')
        self.step('步骤3：截图对比')
        settings_pic = 'settings.jpeg'
        self.take_picture_to_local(settings_pic)
        self.crop_picture(settings_pic)
        similarity = self.compare_image_similarity(settings_pic)
        print_info('相似度为：{}%'.format(similarity))
        self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)
        self.step('步骤4：点击"WLAN"进入WLAN页面')
        # 点击wlan
        self.common_oh.touchByText(self.Phone1, 'WLAN', mode='NORMAL')
        self.common_oh.wait(self.Phone1, 3)
        # 打开wlan
        self.step('步骤5：打开wifi开关')
        self.common_oh.touchByType(self.Phone1, 'Toggle')
        self.common_oh.wait(self.Phone1, 10)
        self.step('步骤6：检查wifi是否打开')
        WifiHelper.checkWifiState(self.Phone1)

    # def enter_setting_page(self):
    #     self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)
    #     self.common_oh.wait(self.Phone1, 5)
    #     self.step('控件检查')
    #     # 控件检查
    #     self.common_oh.checkIfTextExist(self.Phone1, '设置')
    #     self.common_oh.checkIfTextExist(self.Phone1, '搜索设置项')
    #     self.common_oh.checkIfTextExist(self.Phone1, 'WLAN')
    #     self.common_oh.checkIfTextExist(self.Phone1, '声音')
    #     self.common_oh.checkIfTextExist(self.Phone1, '应用')
    #     # 截图对比
    #     self.step('截图对比')
    #     settings_pic = 'settings.jpeg'
    #     self.take_picture_to_local(settings_pic)
    #     self.crop_picture(settings_pic)
    #     similarity = self.compare_image_similarity(settings_pic)[0]
    #     self.step('{}和标准图的相似度为{}%'.format(settings_pic, similarity))
    #     Asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)
    #
    # def enter_wlan_page(self):
    #     self.step('进入WLAN页面')
    #     # 点击wlan
    #     self.common_oh.touchByText(self.Phone1, 'WLAN', mode='NORMAL')
    #     self.common_oh.wait(self.Phone1, 3)
    #     # 打开wlan
    #     toggle = self.common_oh.getWidgetProperties(self.Phone1, 'type/Toggle')
    #     properties = json.loads(toggle)
    #     if properties.get('checked') is False:
    #         self.common_oh.touchByType(self.Phone1, 'Toggle')
    #     self.common_oh.wait(self.Phone1, 5)
    #
    #     wlan_list_pic = 'wlan_list.jpeg'
    #     self.take_picture_to_local(wlan_list_pic)
    #     WifiHelper.checkWifiState(self.Phone1)
    #     # assert WifiHelper.checkWifiState(self.Phone1), AssertionError('failed to turn on wifi')
    #     # self.step('wifi has turned on')
    #
    # def connect_wifi(self):
    #     self.connect_by_click_point()
    #     # 上面的靠坐标点击的方式，容错率低，直接采用Wifi模块
    #     # self.connect_by_wifi_helper()
    #     wifi_pic = 'wifi.jpeg'
    #     self.take_picture_to_local(wifi_pic)
    #     self.common_oh.wait(self.Phone1, 1)
    #     wifi_cs_pic = 'wifi_connection_status.jpeg'
    #     self.take_picture_to_local(wifi_cs_pic)
    #     self.common_oh.wait(self.Phone1, 1)
    #
    # def connect_by_wifi_helper(self):
    #     pwd = 'passw0rd1!'
    #     try:
    #         # WifiHelper.connectWifi(self.Phone1, 'testapold', pwd)
    #         WifiHelper.connectWifi(self.Phone1, 'testapold_Wi-Fi5', pwd)
    #     except:
    #         try:
    #             WifiHelper.connectWifi(self.Phone1, 'testapold', pwd)
    #         except:
    #             pass
    #         # WifiHelper.connectWifi(self.Phone1, 'testapold_Wi-Fi5', pwd)
    #     self.common_oh.wait(self.Phone1, 20)
    #
    # def connect_by_click_point(self):
    #     self.step('点击待连接的wifi')
    #     try:
    #         self.common_oh.touchByText(self.Phone1, 'testapold', mode='NORMAL')
    #     except:
    #         try:
    #             self.common_oh.touchByText(self.Phone1, 'testapold_Wi-Fi5', mode='NORMAL')
    #         except:
    #             pass
    #     try:
    #         self.step('点击密码输入框')
    #         self.common_oh.wait(self.Phone1, 1)
    #         self.common_oh.click(self.Phone1, 200, 200, mode='NORMAL')
    #         self.common_oh.wait(self.Phone1, 1)
    #         for i in range(3):
    #             if self.common_oh.checkIfTextExist(self.Phone1, '?123', 'CONTAINS'):
    #                 # 双击切换到数字输入界面再切回来，使输入法为小写状态
    #                 self.common_oh.click(self.Phone1, 60, 1150, mode='DOUBLE')
    #                 break
    #             elif self.common_oh.checkIfTextExist(self.Phone1, 'ABC', 'CONTAINS'):
    #                 # 双击切换到数字输入界面再切回来，使输入法为小写状态
    #                 self.common_oh.click(self.Phone1, 60, 1150, mode='NORMAL')
    #                 break
    #         # 切换为大写
    #         # self.common_oh.click(self.Phone1, 60, 1040, mode='DOUBLE')
    #         # 密码: passw0rd1!
    #         # P
    #         self.common_oh.click(self.Phone1, 678, 800, mode='NORMAL')
    #         # A
    #         self.common_oh.click(self.Phone1, 80, 920, mode='NORMAL')
    #         # S S
    #         self.common_oh.click(self.Phone1, 150, 920, mode='NORMAL')
    #         self.common_oh.click(self.Phone1, 150, 920, mode='NORMAL')
    #         # W
    #         self.common_oh.click(self.Phone1, 110, 800, mode='NORMAL')
    #         # 切数字输入键盘
    #         self.common_oh.click(self.Phone1, 60, 1150, mode='NORMAL')
    #         # 0
    #         self.common_oh.click(self.Phone1, 678, 800, mode='NORMAL')
    #         # 切回字母输入界面
    #         self.common_oh.click(self.Phone1, 60, 1150, mode='NORMAL')
    #         # self.common_oh.click(self.Phone1, 60, 1040, mode='DOUBLE')
    #         # R
    #         self.common_oh.click(self.Phone1, 250, 800, mode='NORMAL')
    #         # D
    #         self.common_oh.click(self.Phone1, 220, 920, mode='NORMAL')
    #         # 切数字输入键盘
    #         self.common_oh.click(self.Phone1, 60, 1150, mode='NORMAL')
    #         # 1
    #         self.common_oh.click(self.Phone1, 30, 800, mode='NORMAL')
    #         # !
    #         self.common_oh.click(self.Phone1, 500, 1040, mode='NORMAL')
    #         # 点击输入框右边的眼睛查看密码
    #         self.common_oh.click(self.Phone1, 655, 200, mode='NORMAL')
    #         self.common_oh.wait(self.Phone1, 2)
    #         self.take_picture_to_local('password.jpeg')
    #         # 收起输入法
    #         self.common_oh.click(self.Phone1, 675, 700, mode='NORMAL')
    #         self.common_oh.wait(self.Phone1, 2)
    #         # 点击连接
    #         self.common_oh.touchByText(self.Phone1, '连接', mode='NORMAL')
    #         self.common_oh.wait(self.Phone1, 25)
    #     except:
    #         self.step('SmokeTest: wifi list loading error!')

    def teardown(self):
        self.step('收尾1：关闭wifi开关')
        try:
            WifiHelper.closeWifi(self.Phone1)
        except:
            pass
        self.step('收尾2：停掉设置应用')
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
