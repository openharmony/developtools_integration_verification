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
        super().setup()
        self.step('预置条件1：开始相机测试')

    def process(self):
        self.step('步骤1：开启camera hilog')
        self.common_oh.shell(self.Phone1, 'rm -rf /data/log/hilog/* && hilog -b X;hilog -b D -T CAMERA;hilog -r')
        self.common_oh.wait(self.Phone1, 1)
        self.step('步骤2：启动camera app')
        self.common_oh.startAbility(self.Phone1, self.camera_ability_name, self.camera_bundle_name)
        self.common_oh.wait(self.Phone1, 5)
        Asserts.assert_true(self.common_oh.isProcessRunning(self.Phone1, self.camera_bundle_name))
        self.step('步骤3：点击拍照')
        self.common_oh.click(self.Phone1, 360, 1095, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 3)
        self.step('步骤4：切换到录像模式')
        self.common_oh.click(self.Phone1, 430, 980, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤5：点击录制')
        self.common_oh.click(self.Phone1, 360, 1095, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 3)
        self.step('步骤6：停止录制')
        self.common_oh.click(self.Phone1, 320, 1095, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤7：点击左下角切到相册')
        self.common_oh.click(self.Phone1, 200, 1095, mode='NORMAL')
        self.common_oh.wait(self.Phone1, 11)
        self.step('步骤8：hilog打包')
        self.common_oh.shell(self.Phone1, 'cd data/log/hilog/;hilog -x > camera_log.txt;hilog -b D')
        self.common_oh.wait(self.Phone1, 1)
        self.step('步骤9：结果检查')
        self.common_oh.shell(self.Phone1, 'cd /data/log/hilog && grep -nr PreviewOutputCallback')
        self.common_oh.wait(self.Phone1, 1)
        picture_name = 'camera.jpeg'
        self.take_picture_to_local(picture_name)
        self.step('步骤10：检查相册应用是否拉起')
        rst = self.common_oh.shell(self.Phone1, 'aa dump -a | grep {}'.format(self.photo_ability_name))
        self.common_oh.wait(self.Phone1, 5)
        Asserts.assert_in(self.photo_bundle_name, rst)

    def teardown(self):
        self.step('stop camera & photo app')
        self.common_oh.forceStopAbility(self.Phone1, self.camera_bundle_name)
        self.common_oh.cleanApplicationData(self.Phone1, self.camera_bundle_name)
        self.common_oh.forceStopAbility(self.Phone1, self.photo_bundle_name)
        # self.collect_hilog('camera_log.tar')
        self.step('camera test finish')
        super().teardown()

