import logging
import os.path

import cv2


def crop_picture(picture, x1=0, y1=72, x2=720, y2=1208):
    img = cv2.imread(picture)
    img = img[y1:y2, x1:x2]
    cv2.imwrite(picture, img)


def compare_image_similarity(image1, image2):
    logging.info('{} is exist? [{}]'.format(image1, os.path.exists(image1)))
    logging.info('{} is exist? [{}]'.format(image2, os.path.exists(image2)))
    if not os.path.exists(image1) or not os.path.exists(image2):
        logging.info('file not found, set similarity as 0%')
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
        logging.info('no fixture point found, set similarity as 0%')
        return 0
    if not keypoints1:
        if not keypoints2:
            logging.info('similarity is 100%')
            return 1
        logging.info('similarity is 0%')
        return 0
    # 计算相似度
    similarity = len(matches) / len(keypoints1)
    logging.info('similarity is {}%'.format(similarity * 100))
    return similarity
