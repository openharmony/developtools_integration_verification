import logging
import os.path

import cv2


def crop_picture(picture, x1=0, y1=72, x2=720, y2=1208):
    img = cv2.imread(picture)
    img = img[y1:y2, x1:x2]
    cv2.imwrite(picture, img)


def compare_image_similarity(image1, image2):
    logging.info('{}是否存在？[{}]'.format(image1, os.path.exists(image1)))
    logging.info('{}是否存在？[{}]'.format(image2, os.path.exists(image2)))
    if not os.path.exists(image1) or not os.path.exists(image2):
        logging.warning('文件缺失，相似度为0%')
        return 0
    image1 = cv2.imread(image1, 0)
    image2 = cv2.imread(image2, 0)

    # 初始化特征点检测器和描述符
    orb = cv2.ORB_create(edgeThreshold=5, patchSize=30)
    keypoints1, descriptors1 = orb.detectAndCompute(image1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(image2, None)

    # 初始化匹配器
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # 匹配特征点
    matches = bf.match(descriptors1, descriptors2)
    if not matches:
        logging.warning('没有匹配到特征点，相似度为0%')
        return 0
    if not keypoints1:
        if not keypoints2:
            logging.warning('相似度为100%')
            return 1
        logging.warning('相似度为0%')
        return 0
    # 计算相似度
    similarity = len(matches) / len(keypoints1)
    logging.info('相似度为：{}%'.format(similarity * 100))
    return similarity
