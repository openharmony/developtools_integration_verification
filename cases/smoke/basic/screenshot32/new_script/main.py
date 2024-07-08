import argparse
import json
import os.path
import re
import traceback

import pytest

BASE_DIR = os.path.dirname(__file__)


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

        # 报告保存路径
        report = os.path.join(args.save_path, '{}_report.html'.format(sn))
        run_params.extend(['--html={}'.format(report), '--self-contained-html', '--capture=sys'])

        # 用例选择
        selected_cases = distribute_testcase(test_num)
        run_params.extend(selected_cases)

        print(run_params)
        pytest.main(run_params)

        with open(report, 'r+', encoding='gbk') as f:
            text = f.read()
            passed = int(re.findall(r'<span class="passed">(\d+)\s*passed', text, re.I)[0])
            text = text.replace('<meta charset="utf-8"/>', '<meta charset="gbk"/>')
            f.seek(0)
            f.write(text)
        if passed == len(selected_cases):
            print('SmokeTest: End of check, test succeeded!')
        else:
            print('SmokeTest: End of check, SmokeTest find some fatal problems! passed {}/{}'.format(passed, len(selected_cases)))
    except:
        print('SmokeTest: End of check, SmokeTest find some fatal problems! {}'.format(traceback.format_exc()))
