import os

import cv2
import numpy
from PIL import Image
from devicetest.api import Asserts
from devicetest.aw.OpenHarmony import CommonOH
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
        self.STANDARD_SIMILARITY = 55
        self.common_oh = CommonOH
        self.step = Step
        self.asserts = Asserts()

    def take_picture_to_local(self, picture_name):
        """
        将图片从设备上传回本地
        :param picture_name:
        :return:
        """
        self.common_oh.removeFolderByCMD(self.Phone1, '{}*{}'.format(self.device_save_path, picture_name))
        self.common_oh.takePictureByCMD(self.Phone1, '{}{}_{}'.format(self.device_save_path, self.device_name, picture_name))
        self.common_oh.pullFile(self.Phone1, '{}{}_{}'.format(self.device_save_path, self.device_name, picture_name), self.local_save_path)
        self.common_oh.wait(self.Phone1, 1)

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

    def compare_image_similarity(self, picture_name):
        src_image_path = os.path.join(self.local_save_path, '{}_{}'.format(self.device_name, picture_name))
        target_image_path = os.path.join(self.local_resource_path, picture_name)
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

        if isinstance(sub_data, numpy.ndarray):
            sub_data = sub_data[0]
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
