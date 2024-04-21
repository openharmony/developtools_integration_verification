import argparse
import os.path
import shutil
import sys

from xdevice.__main__ import main_process
from xdevice._core.report.result_reporter import ResultReporter
from xml.dom.minidom import parse
# import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)

TEST_CASE_MUST = [
    'Launcher',
    'ProcessCheck',
    #'APLCheck',
    #'ACLCheck',
]

# 根据用例耗时分配的两台设备跑的用例，使两台设备跑的时间都差不多在2min
TEST_CASE_DEVICE1 = [
    #'SettingsWifi',
    #'CrashCheck',
    #'Photos',
    #'Contacts',
    #'Mms',
    #'DistributedMusicPlayer'
]

TEST_CASE_DEVICE2 = [
    #'Camera',
    #'NotificationBar',
    #'Note',
]


def get_test_result(report_path):
    try:
        if not os.path.exists(report_path):
            return False
        rst = ResultReporter.get_task_info_params(report_path)
        unsuccessful_params = rst.get('unsuccessful_params')
        for case, step in unsuccessful_params.items():
            if step:
                return False
        return True
    except:
        return False


# def collect_test_result(report_path):
#     xml_report = os.path.join(report_path, 'summary_report.xml')
#     if not os.path.exists(xml_report):
#         return
#     timestamp = datetime.fromtimestamp(os.path.getmtime(xml_report))
#     test_date = timestamp.strftime('%Y-%m-%d')
#
#     try:
#         dom = parse(xml_report)
#         data = dom.documentElement
#         test_result = {
#             '用例名': [],
#             '测试结果': [],
#             '耗时': [],
#             '报错信息': [],
#             '报告路径': [],
#         }
#         testcases = data.getElementsByTagName('testsuite')
#         testcase_result = []
#         for t in testcases:
#             module_name = t.getAttribute('modulename')
#             result_kind = t.getAttribute('result_kind')
#             time = t.getAttribute('time')
#             testcase = t.getElementsByTagName('testcase')
#             message = testcase[0].getAttribute('message')
#             line = (module_name, result_kind, time, message, xml_report, test_date)
#             if line not in testcase_result:
#                 testcase_result.append(line)
#                 # csv
#                 test_result['用例名'].append(module_name)
#                 test_result['测试结果'].append(result_kind)
#                 test_result['耗时'].append(time)
#                 test_result['报错信息'].append(message)
#                 test_result['报告路径'].append(xml_report)
#
#         df = pd.DataFrame(test_result)
#
#         with open('D:\\smoke_result_{}.csv'.format(test_date), 'a', newline='') as f:
#             df.to_csv(f, header=f.tell() == 0, index=False, mode='a')
#     except:
#         pass
#

if __name__ == '__main__':
    argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description='manual to this scription')
    parser.add_argument('--config', type=str)
    parser.add_argument('--test_num', type=str, default='1/1')
    parser.add_argument('--tools_path', type=str)
    parser.add_argument('--anwser_path', type=str)
    parser.add_argument('--save_path', type=str)
    parser.add_argument('--device_num', type=str)
    parser.add_argument('--pr_url', type=str)
    args = parser.parse_args()

    new_cmd = 'run'
    # 指定设备sn
    if not args.device_num:
        print("SmokeTest: End of check, test failed!")
        sys.exit(98)
    new_cmd += ' -sn {}'.format(args.device_num)
    # 测试用例路径
    tcpath = args.tools_path
    new_cmd += ' -tcpath {}'.format(tcpath)
    # 测试的设备编号，1/1表示只有一台设备；1/2表示第一台设备；2/2表示第二台设备
    if args.test_num == '1/1':
        new_cmd += ' -l {}'.format(';'.join(TEST_CASE_MUST + TEST_CASE_DEVICE1 + TEST_CASE_DEVICE2))
    elif args.test_num == '1/2':
        new_cmd += ' -l {}'.format(';'.join(TEST_CASE_MUST + TEST_CASE_DEVICE1))
    elif args.test_num == '2/2':
        new_cmd += ' -l {}'.format(';'.join(TEST_CASE_MUST + TEST_CASE_DEVICE2))
    # 指定报告生成路径
    report_path = args.save_path
    new_cmd += ' -rp {} -ta screenshot:true'.format(report_path)
    # 测试资源路径
    # respath = args.anwser_path
    # new_cmd += ' -respath {}'.format(respath)
    # shutil.rmtree(os.path.join(BASE_DIR, 'reports'), ignore_errors=True)

    print('SmokeTest Begin >>>>>>>>>>>>')
    main_process(new_cmd)

    # print('SmokeTest collect test result >>>>>>>>>>>>')
    # collect_test_result(report_path)

    print('SmokeTest ending >>>>>>>>>>>>')
    smoke_rst = get_test_result(report_path)
    if smoke_rst:
        print("SmokeTest: End of check, test succeeded!")
        sys.exit(0)
    print("SmokeTest: End of check, test failed!")
    sys.exit(99)
