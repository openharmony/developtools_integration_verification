import logging
import os
import time
import re
import pytest


class Test:


    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        logging.info('ActsStartAbilityStaticTest.hap start')
        hap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(device.resource_path))), 'suites', 'acts', 'acts', 'testcases', 'ActsStartAbilityStaticTest.hap')
        device.install_hap(hap_path)
        output = device.hdc_shell('aa test -b com.acts.startabilitytest.static -m entry -s unittest /ets/testrunner/OpenHarmonyTestRunner -s timeout 15000')
        run = re.search(r'run: (?P<run>\d+),', output)
        passed = re.search(r'Pass: (?P<pass>\d+),', output)
        assert run, '失败'
        assert passed, '失败'
        run_num = int(run.group('run'))
        passed_num = int(passed.group('pass'))
        assert run_num == passed_num, '失败'

    def test_Notification(self, setup_teardown, device):
        logging.info('ActsNotificationCallbackStaticTest.hap start')
        hap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(device.resource_path))), 'suites', 'acts', 'acts', 'testcases', 'ActsNotificationCallbackStaticTest.hap')
        device.install_hap(hap_path)
        output = device.hdc_shell('aa test -b com.acts.startabilitytest.staticcom.example.actsnotificationmanagerrequestenablenotificationcallbacktest.static -m entry -s unittest /ets/testrunner/OpenHarmonyTestRunner -s timeout 15000')
        run = re.search(r'run: (?P<run>\d+),', output)
        passed = re.search(r'Pass: (?P<pass>\d+),', output)
        assert run, '失败'
        assert passed, '失败'
        run_num = int(run.group('run'))
        passed_num = int(passed.group('pass'))
        assert run_num == passed_num, '失败'

    def test_Powermgr(self, setup_teardown, device):
        logging.info('ActsPowermgrDisplayStaticTest.hap start')
        hap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(device.resource_path))), 'suites', 'acts', 'acts', 'testcases', 'ActsPowermgrDisplayStaticTest.hap')
        device.install_hap(hap_path)
        output = device.hdc_shell('aa test -b com.test.display.static -m entry -s unittest /ets/testrunner/OpenHarmonyTestRunner -s timeout 15000')
        run = re.search(r'run: (?P<run>\d+),', output)
        passed = re.search(r'Pass: (?P<pass>\d+),', output)
        assert run, '失败'
        assert passed, '失败'
        run_num = int(run.group('run'))
        passed_num = int(passed.group('pass'))
        assert run_num == passed_num, '失败'