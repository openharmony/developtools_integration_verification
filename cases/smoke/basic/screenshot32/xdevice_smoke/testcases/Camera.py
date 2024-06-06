from devicetest.api import Asserts

from test_case import ITestCase


class Camera(ITestCase):
    camera_ability_name = 'com.ohos.camera.MainAbility'
    camera_bundle_name = 'com.ohos.camera'
    photo_ability_name = 'com.ohos.photos.MainAbility'
    photo_bundle_name = 'com.ohos.photos'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：回到桌面')
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')

    def process(self):
        self.step('步骤1：启动camera app')
        self.common_oh.startAbility(self.Phone1, self.camera_ability_name, self.camera_bundle_name)
        # self.common_oh.wait(self.Phone1, 5)
        self.step('步骤2：点击拍照')
        self.common_oh.click(self.Phone1, 360, 1095, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤3：切换到录像模式')
        self.common_oh.click(self.Phone1, 430, 980, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤4：点击录制')
        self.common_oh.click(self.Phone1, 360, 1095, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 3)
        self.step('步骤5：停止录制')
        self.common_oh.click(self.Phone1, 320, 1095, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        #self.step('步骤6：点击左下角切到相册')
        #self.common_oh.click(self.Phone1, 200, 1095, mode='NORMAL')
        #self.common_oh.wait(self.Phone1, 5)
        #self.step('步骤7：检查相册应用是否拉起')
        #self.common_oh.isProcessRunning(self.Phone1, self.photo_bundle_name)

    def teardown(self):
        self.step('收尾1：停掉相机和相册应用')
        self.common_oh.forceStopAbility(self.Phone1, self.camera_bundle_name)
        self.common_oh.cleanApplicationData(self.Phone1, self.camera_bundle_name)
        self.common_oh.forceStopAbility(self.Phone1, self.photo_bundle_name)
