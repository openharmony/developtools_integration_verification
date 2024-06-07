# -*- coding: utf-8 -*-
# Copyright (c) 2023 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import re
import encodings
import subprocess
import argparse
import os
import cv2
import pytesseract
from ast import parse
from PIL import Image


def enter_cmd(mycmd, waittime):
    if mycmd == "":
        return
    global cmd_retry_cnt
    cmd_retry_cnt = 1
    enter_cmd_retry = 2
    while enter_cmd_retry:
        enter_cmd_retry -= 1
        try:
            p = subprocess.Popen(mycmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result, unused_err = p.communicate(timeout=25)
            try:
                result=result.decode(encoding="utf-8")
            except UnicodeDecodeError:
                result=result.decode('gbk', errors='ignore')
            break
        except Exception as e:
            result = 'retry failed again'
            print(e)
            cmd_retry_cnt += 1
            p.kill()
    if waittime != 0:
        time.sleep(waittime)
    print(result)
    return result


def enter_shell_cmd(shellcmd, waittime, sn):
    global sn1
    global sn2
    if shellcmd == "":
        return
    cmd = "hdc_std -t {} shell \"{}\"".format(sn, shellcmd)
    return enter_cmd(cmd, waittime)


def file_from_dev(src, dst, sn):
    cmd = "hdc_std -t {} file recv \"{}\" \"{}\"".format(sn, src, dst)
    return enter_cmd(cmd, 2)


def get_devices_sn():
    global sn1
    global sn2
    cmd_sn = os.popen("hdc_std list targets").read()
    device_sn = re.findall('[\w+]{32}', cmd_sn)
    sn1 = device_sn[0]
    sn2 = device_sn[1]
    print(sn1)
    print(sn2)


def orc(path):
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'
    tessdata_dir_config = '--tessdata-dir "C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"'
    image = Image.open(path)
    code = pytesseract.image_to_string(image, config=tessdata_dir_config)
    return code


def crop_picture(pic, target, crop_range):
    pic_path = "{}\\{}".format(args.path, pic)
    save_path = "{}\\{}".format(args.path, target)
    im = cv2.imread(pic_path)
    im = im[crop_range[0]:crop_range[1], crop_range[2]:crop_range[3]]
    cv2.imwrite(save_path, im)


def distributed_calc():
    time_one = 1
    time_two = 2
    time_four = 4
    crop_range = [520, 585, 250, 460]
    enter_shell_cmd("aa start -a ohos.samples.distributedcalc.MainAbility -b ohos.samples.distributedcalc",\
        time_four, sn1)
    enter_shell_cmd("uinput -M -m 500 1130 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 500 1130 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 610 110 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 380 1150 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 610 110 -c 0", time_two, sn1)
    enter_shell_cmd("snapshot_display -f /data/distributedcalc.jpeg", time_two, sn1)
    file_from_dev("/data/distributedcalc.jpeg", "{}\\distributedcalc.jpeg".format(args.path), sn1)
    enter_shell_cmd("uinput -M -m 580 1090 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 520 520 -c 0", time_two, sn2)
    enter_shell_cmd("uinput -M -m 520 520 -c 0", time_two, sn2)
    enter_shell_cmd("snapshot_display -f /data/pin.jpeg", time_two, sn2)
    file_from_dev("/data/pin.jpeg", "{}\\pin.jpeg".format(args.path), sn2)
    crop_picture("pin.jpeg", "pin_code.jpeg", crop_range)
    enter_shell_cmd("uinput -M -m 340 530 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 340 530 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 60 1145 -c 0", time_two, sn1)
    code = orc(f"{args.path}\\pin_code.jpeg")
    pin_code = re.findall("[0-9]{6}", code)[0]
    print(pin_code)
    for i in pin_code:
        if i == "0":
            enter_shell_cmd("uinput -M -m 672 800 -c 0", time_one, sn1)
        else:
            j = int(i) - 1
            dx = 42 + j * 70
            enter_shell_cmd(f"uinput -M -m {dx} 800 -c 0", time_one, sn1)
    time.sleep(1)
    enter_shell_cmd("uinput -M -m 60 1145 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 500 600 -c 0", time_two, sn1)
    enter_shell_cmd("killall ohos.samples.distributedcalc", time_two, sn1)
    enter_shell_cmd("aa start -a ohos.samples.distributedcalc.MainAbility -b ohos.samples.distributedcalc",\
        time_four, sn1)
    enter_shell_cmd("uinput -M -m 610 110 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 580 1090 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 580 1090 -c 0", time_two, sn1)
    enter_shell_cmd("uinput -M -m 500 1130 -c 0", time_two, sn2)
    enter_shell_cmd("aa dump -a | grep distributedcalc > /data/distributed_report.txt", time_two, sn2)
    file_from_dev("/data/distributed_report.txt", "{}\\distributed_report.txt".format(args.path), sn2)
    enter_shell_cmd("killall ohos.samples.distributedcalc", time_two, sn2)
    enter_shell_cmd("killall ohos.samples.distributedcalc", time_two, sn1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--path', type=str, default = '.')
    args = parser.parse_args()

    sn1 = ""
    sn2 = ""
    get_devices_sn()
    distributed_calc()