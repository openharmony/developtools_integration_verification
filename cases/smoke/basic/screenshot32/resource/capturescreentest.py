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

from ast import parse
import encodings
import json
import sys
import os
import time
import argparse
import re
import subprocess
import shlex
import datetime
import sqlite3
import shutil
import numpy
import cv2
import pytesseract
from pytesseract import Output
from PIL import Image


def print_to_log(str):
    time = datetime.datetime.now()
    str = "[{}] {}".format(time, str)
    print(str)
    with open(os.path.join(args.save_path, 'test_{}.log'.format(args.device_num)),\
    mode='a', encoding='utf-8') as log_file:
        console = sys.stdout
        sys.stdout = log_file
        print(str)
        sys.stdout = console
    log_file.close()


def enter_cmd(mycmd, waittime=0, printresult=1):
    if mycmd == "":
        return
    global cmd_retry_cnt
    cmd_retry_cnt = 1
    enter_cmdRetry = 2
    while enter_cmdRetry:
        enter_cmdRetry -= 1
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
            print_to_log(e)
            cmd_retry_cnt += 1
            p.kill()
    if printresult == 1:
        with open(os.path.join(args.save_path, 'test_{}.bat'.format(args.device_num)),\
        mode='a', encoding='utf-8') as cmd_f:
            cmd_f.write(mycmd + '\n')
        cmd_f.close()
        print_to_log(mycmd)
        print_to_log(result)
        sys.stdout.flush()
    if waittime != 0:
        time.sleep(waittime)
        if printresult == 1:
            with open(os.path.join(args.save_path, 'test_{}.bat'.format(args.device_num)),\
            mode='a', encoding='utf-8') as cmd_f:
                cmd_f.write("ping -n {} 127.0.0.1>null\n".format(waittime))
            cmd_f.close()
    return result


def enter_shell_cmd(shellcmd, waittime=0, printresult=1):
    if shellcmd == "":
        return
    cmd = "hdc_std -t {} shell \"{}\"".format(args.device_num, shellcmd)
    return enter_cmd(cmd, waittime, printresult)


def sys_exit():
    enter_shell_cmd("cd /data/log/faultlog/temp && tar -cf after_test_cppcrash{}.tar cppcrash*".format(args.device_num))
    file_from_dev("/data/log/faultlog/temp/after_test_cppcrash{}.tar".format(args.device_num), \
    os.path.normpath(args.save_path))
    enter_shell_cmd("cd /data/log/faultlog/faultlogger && tar -cf after_test_jscrash{}.tar jscrash*".format(args.device_num))
    file_from_dev("/data/log/faultlog/faultlogger/after_test_jscrash{}.tar".format(args.device_num), \
    os.path.normpath(args.save_path))
    print_to_log("SmokeTest:: SmokeTest find some key problems!")
    print_to_log("SmokeTest:: End of check, test failed!")
    sys.exit(98)


def file_to_dev(src, dst):
    cmd = "hdc_std -t {} file send \"{}\" \"{}\"".format(args.device_num, src, dst)
    return enter_cmd(cmd, 1, 1)


def file_from_dev(src, dst):
    cmd = "hdc_std -t {} file recv \"{}\" \"{}\"".format(args.device_num, src, dst)
    return enter_cmd(cmd, 1, 1)


def connect_check():
    connection_status = enter_cmd("hdc_std list targets", 2)
    connection_cnt = 0
    while args.device_num not in connection_status and connection_cnt < 15:
        connection_status = enter_cmd("hdc_std list targets", 2)
        connection_cnt += 1
    if connection_cnt == 15:
        print_to_log("SmokeTest:: Device disconnection!!")
        print_to_log("SmokeTest:: End of check, test failed!")
        sys.exit(101)


def sandbox_check(process):
    print_to_log("SmokeTest:: start to check sandbox path")
    medialibrarydata_pidnum = enter_shell_cmd("pgrep -f {}".format(process), 1)
    medialibrarydata_pidnum = medialibrarydata_pidnum.strip()
    sandboxf = enter_shell_cmd("echo \"ls /storage/media/local/\"|nsenter -t {} -m sh".format(medialibrarydata_pidnum), 1)
    if "files" not in sandboxf:
        print_to_log("SmokeTest:: error: can not find sandbox path : /storage/media/local/files")
        return -1
    else:
        print_to_log("SmokeTest:: success: find sandbox path : /storage/media/local/files")
        return 1


def get_coordinate(path, target):
    wifi_numbers = 8
    height = 97
    wifi_range = [236, 286, 45, 300]
    coordinate = []
    img = cv2.imread(path)
    tessdata_dir_config = '--tessdata-dir "C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"'
    while wifi_numbers:
        wifi_range[0] += height
        wifi_range[1] += height
        print_to_log(wifi_range)
        data_img = img[wifi_range[0]:wifi_range[1], wifi_range[2]:wifi_range[3]]
        data = pytesseract.image_to_data(data_img, output_type=Output.DICT, config=tessdata_dir_config, lang='eng')
        for i in range(len(data['text'])):
            if data['text'][i] == target:
                dx = int((wifi_range[2] + wifi_range[3]) / 2)
                dy = int((wifi_range[0] + wifi_range[1]) / 2)
                coordinate.append(dx)
                coordinate.append(dy)
        wifi_numbers -= 1
        if coordinate:
            break
    return coordinate


def connect_wifi(prefix, pic):
    try:
        data = get_coordinate("{}\\{}_{}".format(args.save_path, prefix, pic), "testapold")
        enter_shell_cmd("uinput -M -m {} {} -c 0".format(data[0], data[1]), WAIT_TIME_TWO)
        enter_shell_cmd("uinput -M -m 360 200 -c 0")
        enter_shell_cmd("uinput -M -m 680 810 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 80 910 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 150 910 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 150 910 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 110 810 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 50 1150 -c 0", WAIT_TIME_TWO)
        enter_shell_cmd("uinput -M -m 680 810 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 50 1150 -c 0", WAIT_TIME_TWO)
        enter_shell_cmd("uinput -M -m 250 810 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 220 910 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 50 1150 -c 0", WAIT_TIME_TWO)
        enter_shell_cmd("uinput -M -m 40 810 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 500 1020 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 50 1150 -c 0", WAIT_TIME_ONE)
        enter_shell_cmd("uinput -M -m 680 690 -c 0")
        enter_shell_cmd("snapshot_display -f /data/screen_test/{}".format("testapold.jpeg"))
        file_from_dev("/data/screen_test/{}".format("testapold.jpeg"), args.save_path)
        enter_shell_cmd("uinput -M -m 550 680 -c 0", single_action[0])
    except Exception as e:
        print(e)
        print_to_log("SmokeTest:: wifi list loading errror!")


def calculate(image1, image2):
    image1 = cv2.cvtColor(numpy.asarray(image1), cv2.COLOR_RGB2BGR)
    image2 = cv2.cvtColor(numpy.asarray(image2), cv2.COLOR_RGB2BGR)
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
 
 
def classify_hist_with_split(image1, image2, size=(256, 256)):
    image1 = Image.open(image1)
    image2 = Image.open(image2)
    image1 = cv2.cvtColor(numpy.asarray(image1), cv2.COLOR_RGB2BGR)
    image2 = cv2.cvtColor(numpy.asarray(image2), cv2.COLOR_RGB2BGR)
    image1 = cv2.resize(image1, size)
    image2 = cv2.resize(image2, size)
    sub_image1 = cv2.split(image1)
    sub_image2 = cv2.split(image2)
    sub_data = 0
    for im1, im2 in zip(sub_image1, sub_image2):
        sub_data += calculate(im1, im2)
    sub_data = sub_data / 3
    return sub_data


def crop_picture(prefix, pic, crop_range):
    pic_path = "{}\\{}_{}".format(args.save_path, prefix, pic)
    save_path = "{}\\{}_{}".format(args.save_path, prefix, pic)
    im = cv2.imread(pic_path)
    im = im[crop_range[0]:crop_range[1], crop_range[2]:crop_range[3]]
    cv2.imwrite(save_path, im)


def cmp_picture(prefix, pic, num=1):
    if num == 1:
        img1_path = "{}\\{}".format(args.anwser_path, pic)
    else:
        img1_path = "{}\\2_{}".format(args.anwser_path, pic)
    img2_path = "{}\\{}_{}".format(args.save_path, prefix, pic)
    cmp_init = 0
    try:
        cmp_result = classify_hist_with_split(img1_path, img2_path)
        print("compare result:" + "%.6f%%" % (cmp_result * 100))
        return cmp_result * 100
    except Exception as reason:
        print("no such file: {}_{}".format(prefix, pic))
        return cmp_init


def shot_and_cmp(image):
    prefix = args.device_num
    enter_shell_cmd("snapshot_display -f /data/screen_test/{}_{}".format(prefix, image))
    file_from_dev("/data/screen_test/{}_{}".format(prefix, image), args.save_path)
    similarity = cmp_picture(prefix, image)
    print_to_log("SmokeTest:: launcher similarity is {}%".format(similarity))
    return similarity


def distributed_test():
    if "1/2" in args.test_num or "2/2" in args.test_num:
        report_path = os.path.normpath(os.path.join(args.save_path, "distributed_report.txt"))
        if args.test_num == "2/2":
            enter_shell_cmd("ifconfig eth0 192.168.0.1", WAIT_TIME_ONE)
            ping_result = enter_shell_cmd("ping 192.168.0.2 -i 1 -c 2", 3)
            file_is_exist = enter_shell_cmd("cd /data; find . -name distributed_report.txt")
            ping_cnt = 0
            wait_cnt = 0
            while "2 packets transmitted, 2 received" not in ping_result and ping_cnt < 20:
                ping_result = enter_shell_cmd("ping 192.168.0.2 -i 1 -c 2", WAIT_TIME_FOUR)
                ping_cnt += 1
            if ping_cnt == 30:
                print_to_log("SmokeTest:: Ping failed, timeout of 80s")
                sys_exit()
            while "distributed_report.txt" not in file_is_exist and wait_cnt < 30:
                print_to_log("SmokeTest:: waiting for the distributed test to end ")
                file_is_exist = enter_shell_cmd("cd /data; find . -name distributed_report.txt", WAIT_TIME_FOUR)
                wait_cnt += 1
        elif args.test_num == "1/2":
            enter_shell_cmd("ifconfig eth0 192.168.0.2", WAIT_TIME_ONE)
            ping_result = enter_shell_cmd("ping 192.168.0.1 -i 1 -c 2", WAIT_TIME_FOUR)
            ping_cnt = 0
            while "2 packets transmitted, 2 received" not in ping_result and ping_cnt < 20:
                ping_result = enter_shell_cmd("ping 192.168.0.1 -i 1 -c 2", WAIT_TIME_FOUR)
                ping_cnt += 1
            if ping_cnt == 30:
                print_to_log("SmokeTest:: Ping failed, timeout of 80s")
            print_to_log("SmokeTest:: ##### case 0 : distributed test start #####")
            execute_path = os.path.normpath(os.path.join(args.tools_path, "resource"))
            os.system("cd {} && python distributedtest.py --path {}".format(execute_path, args.save_path))
            distributed_result = ""
            try:
                with open(report_path, mode='r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0)
                    distributed_result = f.read()
                f.close()
            except Exception as reason:
                print_to_log("SmokeTest:: distributed_report.txt is not exist!")
            if "distributedcalc" in distributed_result:
                print_to_log("SmokeTest:: testcase 0, distributed is ok!")
            else:
                print_to_log("SmokeTest:: error:testcase 0, distributed failed!")
                sys_exit()
        enter_shell_cmd("ifconfig eth0 down", WAIT_TIME_ONE)


def open_wlan():
    enter_shell_cmd("aa start -a com.ohos.settings.MainAbility -b com.ohos.settings", WAIT_TIME_FOUR)
    enter_shell_cmd("uinput -M -m 300 300 -c 0", WAIT_TIME_TWO)
    enter_shell_cmd("uinput -M -m 640 200 -c 0", WAIT_TIME_FOUR)
    time.sleep(WAIT_TIME_TWO)
    enter_shell_cmd("killall com.ohos.settings", WAIT_TIME_TWO)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--config', type=str, default = '.\\app_capture_screen_test_config.json')
    parser.add_argument('--test_num', type=str, default = '1/1')
    parser.add_argument('--tools_path', type=str, default = 'D:\\DeviceTestTools\\screenshot\\')
    parser.add_argument('--anwser_path', type=str, default = 'D:\\DeviceTestTools\\screenshot\\resource')
    parser.add_argument('--save_path', type=str, default = 'D:\\DeviceTestTools\\screenshot')
    parser.add_argument('--device_num', type=str, default = 'null')
    parser.add_argument('--pr_url', type=str, default = 'developtools_integration_verification')
    args = parser.parse_args()

    if args.device_num == 'null':
        result = enter_cmd("hdc_std list targets", 1, 0)
        print(result)
        args.device_num = result.split()[0]
    with open(args.config) as f:
        all_app = json.load(f)
    cmp_status = 0
    global_pos = all_app[0]
    
    WAIT_TIME_ONE = 1
    WAIT_TIME_TWO = 2
    WAIT_TIME_FOUR = 4

    reboot_cnt = 2
    while reboot_cnt:
        reboot_cnt -= 1
        enter_shell_cmd("mkdir -p /data/screen_test/train_set")
        rmlock_cnt = 3
        while rmlock_cnt:
            enter_shell_cmd("uinput -T -m 425 1000 425 400;power-shell wakeup;uinput -T -m 425 400 425 1000;\
            power-shell setmode 602;uinput -T -m 425 1000 425 400;", WAIT_TIME_ONE)
            rmlock_cnt -= 1
        enter_shell_cmd("hilog -w stop", WAIT_TIME_ONE)
        enter_shell_cmd("cd /data/log/hilog && tar -cf system_start_log_{}.tar *".format(args.device_num), WAIT_TIME_ONE)
        file_from_dev("/data/log/hilog/system_start_log_{}.tar".format(args.device_num), args.save_path)
        connect_check()
        launcher_similarity = shot_and_cmp("launcher.jpeg")
        if launcher_similarity >= 90:
            print_to_log("SmokeTest:: launcher screenshot comparison is ok!")
            break
        elif reboot_cnt >= 1:
            print_to_log("SmokeTest:: launcher screenshot comparison failed, reboot and try!!!")
            enter_shell_cmd("rm -rf /data/*;reboot")
            for i in range(5):
                enter_cmd("hdc_std list targets", 10)
        else:
            print_to_log("SmokeTest:: launcher screenshot comparison failed")
            sys_exit()

    enter_shell_cmd("cat /proc/`pidof foundation`/smaps_rollup")

    print_to_log("\nSmokeTest:: ########## First check key processes start ##############")
    lose_process = []
    process_pid = {}
    with open(os.path.normpath(os.path.join(args.tools_path, "resource/process.txt")), "r+") as f:
        text = f.read()
        two_check_process_list = text.split('#####')[1].split()[0:-1]
        other_process_list = text.split('#####')[2].split()
        for pname in two_check_process_list:
            pids = enter_cmd("hdc_std -t {} shell pidof {}".format(args.device_num, pname), 0, 1)
            try:
                pidlist = pids.split()
                int(pidlist[0])
                for pid in pidlist:
                    int(pid)
                process_pid[pname] = pidlist
            except:
                lose_process.append(pname)
        all_p = enter_shell_cmd("ps -elf")
        for pname in other_process_list:
            findp = all_p.find(pname, 0, len(all_p))
            if findp == -1:
                lose_process.append(pname)

    if lose_process:
        print_to_log("SmokeTest:: error: %s, These processes are not exist!!!" % lose_process)
        sys_exit()
    else:
        print_to_log("SmokeTest:: first processes check is ok")

    power_state = enter_shell_cmd("hidumper -s 3308", WAIT_TIME_ONE)
    if "State=2" not in power_state:
        print_to_log("SmokeTest:: DISPLAY POWER MANAGER DUMP State=0")
        sys_exit()

    open_wlan()

    special_warehouse = [
        "arkui_ace_engine",
        "developtools_integration_verification",
        "graphic_graphic_2d",
        "windowmanager"]

    for warehouse in special_warehouse:
        if warehouse in args.pr_url:
            if args.test_num == "1/2":
                args.test_num = "3/2"
            elif args.test_num == "2/2":
                args.test_num = "4/2"
    print(args.pr_url)
    try:
        args.test_num.index('/')
        idx_total = args.test_num.split('/')
        if len(idx_total) != 2:
            print_to_log("SmokeTest:: test_num is invaild !!!")
            sys_exit()
        elif idx_total[1] == '1':
            idx_list = list(range(1, len(all_app)))
        else:
            idx_list = global_pos['DEVICE_{}'.format(idx_total[0])]
    except ValueError as e:
        print_to_log(e)
        idx_list = list(map(eval, args.test_num.split()))
    print_to_log("SmokeTest:: start to carry out the following testcases: ")
    print_to_log("SmokeTest:: testcase number: {} ".format(idx_list))

    fail_idx_list = []
    fail_name_list = []
    smoke_first_failed = ''
    for idx in idx_list:
        single_app = all_app[idx]
        sys.stdout.flush()
        call_app_cmd = single_app['entry']
        capture_screen_cmd = "snapshot_display -f /data/screen_test/{}_{}"
        print_to_log("\nSmokeTest:: ##### case {} : {} test start #####".format(idx, single_app['app_name']))
        with open(os.path.join(args.save_path, 'test_{}.bat'.format(args.device_num)),\
        mode='a', encoding='utf-8') as cmd_f:
            cmd_f.write("\nSmokeTest::::::case {} --- {} test start \n".format(idx, single_app['app_name']))
        cmd_f.close()
        testcnt = 3
        while testcnt:
            testok = 0
            if testcnt != 3:
                print_to_log("SmokeTest:: this testcase try again >>>>>>:\n")
                with open(os.path.join(args.save_path, 'test_{}.bat'.format(args.device_num)),\
                mode='a', encoding='utf-8') as cmd_f:
                    cmd_f.write("\nSmokeTest::::::Last failed, try again \n")
                cmd_f.close()
            if idx == 1:
                testcnt = 1
            if single_app['entry'] != "":
                enter_shell_cmd(call_app_cmd, WAIT_TIME_FOUR)
            print_to_log("SmokeTest:: execute command {}".format(single_app['all_actions']))
            prefix = args.device_num
            raw_pic_name = ''
            pic_name = ''
            for single_action in single_app['all_actions']:
                if type(single_action[1]) == str and single_action[1] == 'shot_cmd':
                    if len(single_action) == 3:
                        pic_name = "{}{}".format(single_action[2], ".jpeg")
                    else:
                        pic_name = "{}{}".format(single_app['app_name'], ".jpeg")
                    enter_shell_cmd("rm /data/screen_test/*{}".format(pic_name), WAIT_TIME_ONE)
                    enter_shell_cmd(capture_screen_cmd.format(prefix, pic_name), WAIT_TIME_ONE)
                    file_from_dev("/data/screen_test/{}_{}".format(prefix, pic_name), args.save_path)
                    next_cmd = ""
                elif type(single_action[1]) == str and single_action[1] == 'cmp_twice':
                    next_cmd = ""
                    sys.stdout.flush()
                    pic = "{}{}".format(single_action[2], ".jpeg")
                    similarity = single_action[3]
                    crop_range = single_app[single_action[4]]
                    crop_picture(prefix, pic, crop_range)
                    first_similarity = cmp_picture(prefix, pic)
                    second_similarity = cmp_picture(prefix, pic, WAIT_TIME_TWO)
                    print_to_log("SmokeTest:: first picture similarity is {}%".format(first_similarity))
                    print_to_log("SmokeTest:: second picture similarity is {}%".format(second_similarity))
                    if first_similarity >= similarity or second_similarity >= similarity:
                        if testok != -1:
                            testok = 1
                        print_to_log("SmokeTest:: {} screenshot check is ok".format(pic))
                    else:
                        testok = -1
                        print_to_log("SmokeTest:: {} screenshot check is abnarmal".format(pic))
                elif type(single_action[1]) == str and single_action[1] == 'cmp_cmd-level':
                    next_cmd = ""
                    sys.stdout.flush()
                    if len(single_action) == 4:
                        similarity = single_action[3]
                    else:
                        similarity = global_pos['cmp_cmd-level'][1]
                        similarity = int(similarity)
                    print_to_log("SmokeTest:: start to contrast screenshot")
                    pic = "{}{}".format(single_action[2], ".jpeg")
                    crop_range = [80, 1200, 0, 720]
                    crop_picture(prefix, pic, crop_range)
                    pic_similarity = cmp_picture(prefix, pic)
                    print_to_log("SmokeTest:: picture similarity is {}%".format(pic_similarity))
                    if len(single_action) >= 3:
                        if pic_similarity >= similarity:
                            if testok != -1:
                                testok = 1
                            print_to_log("SmokeTest:: {} screenshot check is ok".format(pic))
                        else:
                            testok = -1
                            print_to_log("SmokeTest:: {} screenshot check is abnarmal".format(pic))
                elif type(single_action[1]) == str and single_action[1] == 'install_hap':
                    next_cmd = ""
                    if len(single_action) == 3:
                        enter_cmd("hdc_std -t {} install \"{}\"".format(args.device_num,\
                        os.path.normpath(os.path.join(args.tools_path, single_action[2]))))
                elif type(single_action[1]) == str and single_action[1] == 'get_file_from_dev':
                    next_cmd = ""
                    if len(single_action) == 3:
                        enter_cmd("hdc_std -t {} file recv \"{}\" \"{}\"".format(args.device_num,\
                        single_action[2], os.path.normpath(args.save_path)))
                elif type(single_action[1]) == str and single_action[1] == 'send_file_to_dev':
                    next_cmd = ""
                    if len(single_action) == 4:
                        enter_cmd("hdc_std -t {} file send \"{}\" \"{}\"".format(args.device_num,\
                        os.path.normpath(os.path.join(args.tools_path, single_action[2])), single_action[3]))
                elif type(single_action[1]) == str and single_action[1] == 'connect_wifi':
                    next_cmd = ""
                    pic = "{}{}".format(single_action[2], ".jpeg")
                    connect_wifi(prefix, pic)
                elif type(single_action[1]) == str and single_action[1] == 'sandbox_path_check':
                    next_cmd = ""
                    if sandbox_check("com.ohos.medialibrary.medialibrarydata") == 1 and testok == 1:
                        testok = 1
                    else:
                        testok = -1
                elif type(single_action[1]) == str and single_action[1] == 'process_crash_check':
                    next_cmd = ""
                    if len(single_action) == 3:
                        p = enter_shell_cmd("cd /data/log/faultlog/temp && grep \"Process name\" -rnw ./",\
                        single_action[0])
                        result = "".join(p)
                        findsome = result.find(single_action[2], 0, len(result))
                        if findsome != -1:
                            testok = -1
                            print_to_log("SmokeTest:: \"{}\" error:find fatal crash \"{}\"!".format(single_action[1],\
                            single_action[2]))
                            sys_exit()
                        else:
                            testok = 1
                            print_to_log("SmokeTest:: \"{}\" result is ok, not find fatal\
                            crash \"{}\"!".format(single_action[1], single_action[2]))
                        sys.stdout.flush()
                elif type(single_action[1]) == str:
                    if single_action[1] not in single_app.keys():
                        target_ = global_pos[single_action[1]]
                    else:
                        target_ = single_app[single_action[1]]
                    if type(target_[0]) == str:
                        next_cmd = ""
                        p = enter_shell_cmd(target_[0], single_action[0])
                        result = "".join(p)
                        if len(target_) > 1:
                            findsome = result.find(target_[1], 0, len(result))
                            if findsome != -1:
                                testok = 1
                                print_to_log("SmokeTest:: \"{}\" check result is ok, find \"{}\"!".format(target_[0],\
                                target_[1]))
                            else:
                                testok = -1
                                print_to_log("SmokeTest:: \"{}\" result is not ok, not find \"{}\"!".format(target_[0],\
                                target_[1]))
                            sys.stdout.flush()
                    else:
                        next_cmd = "uinput -M -m {} {} -c 0".format(target_[0], target_[1])
                else:
                    next_cmd = "uinput -M -m {} {} -c 0".format(single_action[1], single_action[2])
                enter_shell_cmd(next_cmd, single_action[0])

            if testok == 1:
                print_to_log("SmokeTest:: testcase {}, {} is ok!".format(idx, single_app['app_name']))
                testcnt = 0
            elif testok == -1 and smoke_first_failed == '':
                if testcnt == 1:
                    fail_idx_list.append(idx)
                    fail_name_list.append(single_app['app_name'])
                    smoke_first_failed = single_app['app_name']
                    print_to_log("SmokeTest:: error:testcase {}, {} is failed!".format(idx, single_app['app_name']))
                testcnt -= 1
            elif testok == -1 and smoke_first_failed != '':
                fail_idx_list.append(idx)
                fail_name_list.append(single_app['app_name'])
                print_to_log("SmokeTest:: error:testcase {}, {} is failed!".format(idx, single_app['app_name']))
                testcnt = 0
            else:
                testcnt = 0
            connect_check()

    enter_shell_cmd("cd /data/log/faultlog/temp && grep \"Process name\" -rnw ./", 1)
    enter_shell_cmd("cd /data/log/faultlog/faultlogger && grep \"Process name\" -rnw ./", 1)

    fail_str_list = [str(x) for x in fail_idx_list]
    reboot_test_num = " ".join(fail_str_list)
    if len(fail_idx_list) != 0:
        print_to_log("SmokeTest:: failed testcase number: {} ".format(fail_str_list))
        print_to_log("SmokeTest:: check \"reboot\" in reboot.txt".format(args.save_path))
        with open(os.path.normpath(os.path.join(args.tools_path, "reboot.txt")), mode='a+') as f:
            f.seek(0)
            reboot_result = f.read()
        f.close()
        if len(reboot_result) < 1 and reboot_cnt >= 1:
            print_to_log("SmokeTest:: \"reboot\" is not found in the reboot.txt")
            print_to_log("SmokeTest:: the device will reboot and try the failed testcase")
            print_to_log("SmokeTest:: mkdir {}\\reboot".format(args.save_path))
            os.system("mkdir {}\\reboot".format(args.save_path))
            print_to_log("SmokeTest:: write \"reboot\" into reboot.txt".format(args.save_path))
            with open(os.path.normpath(os.path.join(args.tools_path, "reboot.txt")), mode='w') as f:
                f.write("reboot")
            f.close()
            print_to_log("SmokeTest:: error: name {}, index {}, failed, rm /data/* and reboot".format(fail_name_list,\
            fail_idx_list))
            enter_shell_cmd("rm -rf /data/* && reboot")
            reboot_result_list = enter_cmd("hdc_std list targets", 2)
            number = 0
            while args.device_num not in reboot_result_list and number < 15:
                reboot_result_list = enter_cmd("hdc_std list targets", 2)
                number += 1
            enter_shell_cmd("rm /data/log/hilog/*;hilog -r;hilog -w start -l 400000000 -m none", 1)
            py_cmd = os.system("python {}\\resource\\capturescreentest.py --config \
            {}\\resource\\app_capture_screen_test_config.json --anwser_path {} \
            --save_path {}\\reboot --tools_path {} --device_num {} --test_num \"{}\"".format(args.tools_path, \
            args.tools_path, args.anwser_path, args.save_path, args.tools_path, args.device_num, reboot_test_num))
            if py_cmd == 0:
                sys.exit(0)
            elif py_cmd == 98:
                sys.exit(98)
            else:
                sys.exit(101)
        else:
            print_to_log("SmokeTest:: error: name {}, index {}, these testcase is failed".format(fail_name_list,\
            fail_idx_list))
            sys_exit()
    else:
        print_to_log("SmokeTest:: all testcase is ok")
        print_to_log("SmokeTest:: End of check, test succeeded!")
        sys.exit(0)
