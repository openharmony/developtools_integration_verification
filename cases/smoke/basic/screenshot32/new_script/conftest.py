import logging
import os.path

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
    logging.info('前置操作')
    current_case = os.path.basename(request.path)[:-3]
    # 日志截图等保存路径
    device.report_path = os.path.realpath(os.path.dirname(request.config.option.htmlpath))
    logging.info('设置当前用例的报告路径为{}'.format(device.report_path))
    device.resource_path = os.path.join(os.path.dirname(__file__), 'resource')
    os.makedirs(device.report_path, exist_ok=True)
    # device.rm_faultlog()
    # device.start_hilog()
    device.wakeup()
    device.set_screen_timeout()
    device.unlock()
    device.go_home()
    if device.get_focus_window() == 'SystemDialog1':
        device.click(360, 715)

    yield

    logging.info('后置操作')
    device.go_home()
    logging.info('点击右下角多任务键清理所有任务')
    device.clear_recent_task()
    device.clean_app_data(request.param)
    # device.stop_and_collect_hilog()
