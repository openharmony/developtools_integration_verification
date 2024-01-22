import os

import cv2
import numpy
from PIL import Image
from devicetest.aw.OpenHarmony import CommonOH
from devicetest.controllers.cv import compare_image_similarity
from devicetest.core.test_case import TestCase, Step


class ITestCase(TestCase):

    def __init__(self, controllers):
        self.TAG = self.__class__.__name__
        TestCase.__init__(self, self.TAG, controllers)
        self.device_name = self.Phone1.device_sn
        # path 相关
        self.device_save_path = '/data/local/tmp/screen_test/'
        self.testcases_path = os.path.dirname(__file__)
        self.local_resource_path = os.path.join(os.path.dirname(self.testcases_path), 'resource')
        self.local_save_path = self.cur_case.case_screenshot_dir
        if not os.path.exists(self.local_save_path):
            os.makedirs(self.local_save_path, exist_ok=True)
        # framework utils
        self.STANDARD_SIMILARITY = 60
        self.common_oh = CommonOH
        self.step = Step
        self.step('testcase path is: {}'.format(self.testcases_path))
        self.step('local resource path is: {}'.format(self.local_resource_path))
        self.step('local save path is: {}'.format(self.local_save_path))

    def setup(self):
        self.common_oh.wake(self.Phone1)
        self.common_oh.goHome(self.Phone1)
        self.step('start log')
        # self.common_oh.shell(self.Phone1, 'rm -rf /data/log/hilog/* && hilog -r && hilog -Q pidoff;hilog -G 512M;hilog -w start -l 400000000 -m none')
        self.common_oh.wait(self.Phone1, 1)

    def take_picture_to_local(self, picture_name):
        """
        将图片从设备上传回本地
        :param picture_name:
        :return:
        """
        self.step('delete history screen shot picture')
        self.common_oh.removeFolderByCMD(self.Phone1, '{}*{}'.format(self.device_save_path, picture_name))
        self.step('shot new picture')
        self.common_oh.takePictureByCMD(self.Phone1, '{}{}_{}'.format(self.device_save_path, self.device_name, picture_name))
        self.step('pull picture to local')
        self.common_oh.pullFile(self.Phone1, '{}{}_{}'.format(self.device_save_path, self.device_name, picture_name), self.local_save_path)
        self.common_oh.wait(self.Phone1, 2)

    # def compare_image_similarity(self, picture_name, similar=0.95):
    #     """
    #     :param picture_name:
    #     :param similar:
    #     :return:
    #     """
    #     src_image_path = os.path.join(self.local_save_path, '{}_{}'.format(self.device_name, picture_name))
    #     target_image_path = os.path.join(self.local_resource_path, picture_name)
    #     self.step('compare picture: {}>>>'.format(picture_name))
    #     self.step('src image path({}) exist?{}'.format(src_image_path, os.path.exists(src_image_path)))
    #     self.step('target image path({}) exist?{}'.format(target_image_path, os.path.exists(target_image_path)))
    #     return compare_image_similarity(self.Phone1, src_image_path, target_image_path, similar)

    def crop_picture(self, picture, crop_range=None):
        """
        对图片进行裁剪
        :param picture:待裁剪的图片路径
        :param crop_range: 裁剪的尺寸，如[80, 1200, 0, 720] 表示纵向80~1200，横向0~720的裁剪范围，基本就是去掉上面的状态栏和下面的导航栏
        :return:
        """
        picture = os.path.join(self.local_save_path, '{}_{}'.format(self.device_name, picture))
        if crop_range is None:
            crop_range = [80, 1200, 0, 720]
        img = cv2.imread(picture)
        img = img[crop_range[0]: crop_range[1], crop_range[2]: crop_range[3]]
        cv2.imwrite(picture, img)

    def teardown(self):
        self.common_oh.goHome(self.Phone1)

    def collect_hilog(self, log_name):
        self.step('stop hilog')
        self.common_oh.shell(self.Phone1, 'hilog -w stop')
        self.common_oh.wait(self.Phone1, 1)
        self.step('compress hilog')
        self.common_oh.shell(self.Phone1, 'cd /data/log/hilog && tar -cf {} *'.format(log_name))
        self.common_oh.wait(self.Phone1, 1)
        self.step('transfer {} from device to {}'.format(log_name, self.local_save_path))
        self.common_oh.pullFile(self.Phone1, '/data/log/hilog/{}'.format(log_name), os.path.normpath(self.local_save_path))
        self.common_oh.wait(self.Phone1, 1)

    def compare_image_similarity(self, picture_name):
        src_image_path = os.path.join(self.local_save_path, '{}_{}'.format(self.device_name, picture_name))
        target_image_path = os.path.join(self.local_resource_path, picture_name)
        self.step('compare picture: {}>>>'.format(picture_name))
        self.step('src image path({}) exist?{}'.format(src_image_path, os.path.exists(src_image_path)))
        self.step('target image path({}) exist?{}'.format(target_image_path, os.path.exists(target_image_path)))

        size = (256, 256)
        image1 = Image.open(src_image_path)
        image2 = Image.open(target_image_path)
        image1 = cv2.cvtColor(numpy.asarray(image1), cv2.COLOR_RGB2BGR)
        image2 = cv2.cvtColor(numpy.asarray(image2), cv2.COLOR_RGB2BGR)
        image1 = cv2.resize(image1, size)
        image2 = cv2.resize(image2, size)
        sub_image1 = cv2.split(image1)
        sub_image2 = cv2.split(image2)
        sub_data = 0
        for im1, im2 in zip(sub_image1, sub_image2):
            sub_data += self.__calculate__(im1, im2)
        sub_data = sub_data / 3
        return sub_data * 100

    def __calculate__(self, img1, img2):
        image1 = cv2.cvtColor(numpy.asarray(img1), cv2.COLOR_RGB2BGR)
        image2 = cv2.cvtColor(numpy.asarray(img2), cv2.COLOR_RGB2BGR)
        hist1 = cv2.calcHist([image1], [0], None, [256], [0.0, 255.0])
        hist2 = cv2.calcHist([image2], [0], None, [256], [0.0, 255.0])
        degree = 0
        for i in range(len(hist1)):
            if hist1[i] != hist2[i]:
                degree = degree + (1 - abs(hist1[i] - hist2[i]) / max(hist1[i], hist2[i]))
            else:
                degree = degree + 1
        degree = degree / len(hist1)
        return degree
