# -*- coding: utf-8 -*-
import os.path

from devicetest.api import Asserts

from test_case import ITestCase


class VideoTest(ITestCase):
    bundle_name = 'ohos.acts.multimedia.video.videoplayer'

    def __init__(self, controllers):
        super().__init__(controllers)
        self.video_hap_path = os.path.join(self.local_resource_path, 'videotest', 'ActsVideoPlayerJsTest.hap')
        self.mp4_path = os.path.join(self.local_resource_path, 'videotest', 'H264_AAC.mp4')

    def setup(self):
        super().setup()
        self.step('预置条件：VideoTest测试开始')

    def process(self):
        self.step('步骤1：安装video hap')
        self.common_oh.installApp_r(self.Phone1, self.video_hap_path)
        self.common_oh.wait(self.Phone1, 2)
        self.step('步骤2：创建目录')
        self.common_oh.shell(self.Phone1, 'mkdir -p /data/app/el2/100/base/{}/haps/entry/files'.format(self.bundle_name))
        self.common_oh.wait(self.Phone1, 1)
        self.step('步骤3：remount')
        self.common_oh.shell(self.Phone1, 'mount -o rw,remount')
        self.common_oh.wait(self.Phone1, 1)
        self.step('步骤4：send file to device')
        dev_path = '/data/app/el2/100/base/ohos.acts.multimedia.video.videoplayer/haps/entry/files/'
        self.common_oh.pushFile(self.Phone1, self.mp4_path, dev_path)
        self.common_oh.wait(self.Phone1, 1)
        cmd = 'aa test -p {} -b {} -s unittest OpenHarmonyTestRunner -w 2000000 -s timeout 60000'.format(self.bundle_name, self.bundle_name)
        result = self.common_oh.shell(self.Phone1, cmd)
        self.common_oh.wait(self.Phone1, 5)
        key_words = 'Failure: 0, Error: 0, Pass: 1'
        Asserts.assert_true(key_words in result)

    def teardown(self):
        self.step('收尾：停止Video app')
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
        # self.collect_hilog('video_log.tar')
        self.step('VideoTest finish')
        super().teardown()
