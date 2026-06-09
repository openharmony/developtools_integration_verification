#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Huawei Device Co., Ltd.
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
#

import logging
import re

import pytest


class Test:
    pid_list = [
        'com.ohos.launcher',
        'render_service',
    ]

    ps_list = [
        'hdf_devmgr',
        'param_watcher',
        'storage_manager',
        'appspawn',
        'hilogd',
        'samgr',
        'storage_daemon',
        'uinput_inject',
        'multimodalinput',
        'huks_service',
        'memmgrservice',
        'bluetooth_servi',
        'resource_schedu',
        'audio_server',
        'softbus_server',
        'faultloggerd',
        'accountmgr',
        'time_service',
        'distributeddata',
        'useriam',
        'inputmethod_ser',
        'ui_service',
        'netmanager',
        'sensors',
        'media_service',
        'wifi_manager_se',
        'installs',
        'hiview',
        'telephony',
        'camera_service',
        'foundation',
        'hdcd',
        'light_host',
        'vibrator_host',
        'sensor_host',
        'input_user_host',
        'camera_host',
        'audio_host',
        'wifi_host',
        'usb_host',
        'blue_host',
        'com.ohos.systemui',
        'power_host',
    ]

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        lost_process = []
        logging.info('check pid is exist or not')
        for process in self.pid_list:
            pid = device.get_pid(process)
            if not re.search(r'\d+', pid):
                lost_process.append(process)

        ps_elf_rst = device.hdc_shell('ps -elf')
        for pname in self.ps_list:
            if pname not in ps_elf_rst:
                lost_process.append(pname)

        logging.info('lost process are {}'.format(lost_process))
        assert not lost_process
