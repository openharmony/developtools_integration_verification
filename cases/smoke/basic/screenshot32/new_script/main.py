import argparse
import json
import os.path
import re
import sys
import traceback

import pytest

BASE_DIR = os.path.dirname(__file__)

parser = argparse.ArgumentParser(description='manual to this scription')
parser.add_argument('--test_num', type=str, default='1/1')
parser.add_argument('--save_path', type=str, default='./report')
parser.add_argument('--device_num', type=str, default='')
args = parser.parse_args()

run_params = ['-vs']

try:
    sn = args.device_num
    run_params.append('--sn={}'.format(sn))

    # 报告保存路径
    report = os.path.join(args.save_path, sn, 'report.html')
    run_params.append('--html={}'.format(report))

    with open(os.path.join(BASE_DIR, 'testcases.json'), 'r', encoding='utf-8') as f:
        test_cases_list = [case.get('case_file') for case in json.load(f)]
    test_num = args.test_num
    if test_num == '1/2':
        selected_case = test_cases_list[0:1] + test_cases_list[8:]
    elif test_num == '2/2':
        selected_case = test_cases_list[0:8]
    else:
        selected_case = test_cases_list

    run_params.extend(selected_case)
    print(run_params)
    pytest.main(run_params)
    print('获取测试结果')
    with open(report, 'r', encoding='utf-8') as f:
        text = f.read()
        passed = int(re.findall(r'<span class="passed">(\d+) Passed,</span>', text)[0])

    if passed == len(selected_case):
        print('SmokeTest: End of check, test succeeded!')
        sys.exit(0)
    else:
        print('SmokeTest: End of check, SmokeTest find some fatal problems! passed {}/{}'.format(passed, len(selected_case)))
        sys.exit(98)
except:
    print('SmokeTest: End of check, SmokeTest find some fatal problems! {}'.format(traceback.format_exc()))
    sys.exit(98)
