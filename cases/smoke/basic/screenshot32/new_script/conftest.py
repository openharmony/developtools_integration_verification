import logging
import os.path
import time

import pytest

from utils.device import Device

BASE_DIR = os.path.dirname(__file__)


def pytest_addoption(parser):
    parser.addoption('--sn', default='')


@pytest.fixture(scope='session', autouse=True)
def device(request):
    sn = request.config.option.sn
    return Device(sn)


@pytest.fixture(scope='module')
def setup_teardown(request, device):
    # logging.info('setup--------')
    current_case = os.path.basename(request.path)[:-3]
    # 日志截图等保存路径
    device.report_path = os.path.realpath(os.path.dirname(request.config.option.htmlpath))
    logging.info('set current report path as {}'.format(device.report_path))
    device.resource_path = os.path.join(os.path.dirname(__file__), 'resource')
    os.makedirs(device.report_path, exist_ok=True)
    # device.rm_faultlog()
    # device.start_hilog()
    device.wakeup()
    device.unlock()
    time.sleep(2)
    device.set_power_mode()
    device.set_screen_timeout()
    device.unlock()
    time.sleep(5)
    #device.go_home()
    time.sleep(1)
    if device.get_focus_window() == 'SystemDialog1':
        device.click(360, 800)
        time.sleep(2)
    #if device.get_focus_window() == 'SystemDialog1':
    #    rst = self.hdc_shell(f'ps -ef | grep -w com.ohos.systemui | grep -v grep')
    #    rst_list = rst.split()
    #     logging.info(f'Process ID: {rst_list[1]}')
    #     device.hdc_shell(f'kill -9 {rst_list[1]}')
    #     #device.click(595, 555)
    #     time.sleep(5)
    #     device.unlock()

    device.click(360, 1245)
    time.sleep(1)
    #device.click(360, 1245)


    yield

    # logging.info('后置操作')
    device.go_home()
    logging.info('clear recent task')
    device.clear_recent_task()
    device.clean_app_data(request.param)
    # device.stop_and_collect_hilog()
