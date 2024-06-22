import argparse
import json
import os.path
import re
import shutil
import socket
import traceback

import pytest

BASE_DIR = os.path.dirname(__file__)


def report_content(sn, pr):
    hostname = socket.gethostname()
    ipaddress = socket.gethostbyname(hostname)
    return [
        '--report=_{}_reports.html'.format(sn),
        '--title=门禁冒烟测试报告',
        '--tester={}'.format(ipaddress),
        '--desc={}'.format(pr),
        '--template=1'
    ]


def distribute_testcase(test_num):
    with open(os.path.join(BASE_DIR, 'testcases.json'), 'r', encoding='utf-8') as f:
        test_cases_list = [case.get('case_file') for case in json.load(f)]
    if test_num == '1/2':
        selected = test_cases_list[0:1] + test_cases_list[8:]
    elif test_num == '2/2':
        selected = test_cases_list[0:8]
    else:
        selected = test_cases_list
    return selected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='manual to this scription')
    parser.add_argument('--test_num', type=str, default='1/1')
    parser.add_argument('--save_path', type=str, default='./report')
    parser.add_argument('--device_num', type=str, default='')
    parser.add_argument('--pr', type=str, default='')
    args = parser.parse_args()

    test_num = args.test_num
    sn = args.device_num
    save_path = os.path.join(args.save_path, sn)
    pr = args.pr

    print('[current dir]{}'.format(os.getcwd()))

    run_params = ['-vs', '--sn={}'.format(sn)]

    try:
        # 用例选择
        cases = distribute_testcase(test_num)
        run_params.extend(cases)
        # 报告保存路径
        report = report_content(sn, pr)
        run_params.extend(report)

        report_dir = os.path.join(BASE_DIR, 'reports')
        try:
            shutil.rmtree(report_dir)
        except:
            pass

        print(run_params)
        pytest.main(run_params)
        try:
            shutil.copytree(report_dir, save_path)
        except:
            pass
        html_file = [f for f in os.listdir(report_dir) if f.endswith('{}_reports.html')][0]

        with open(os.path.join(report_dir, html_file), 'r', encoding='utf-8') as f:
            text = f.read()

            passed = int(re.findall(r'<span class="text-success">\s*(\d+)\s*</span>', text)[0])
        if passed == len(cases):
            print('SmokeTest: End of check, test succeeded!')
        else:
            print('SmokeTest: End of check, SmokeTest find some fatal problems! passed {}/{}'.format(passed, len(cases)))
    except:
        print('SmokeTest: End of check, SmokeTest find some fatal problems! {}'.format(traceback.format_exc()))
