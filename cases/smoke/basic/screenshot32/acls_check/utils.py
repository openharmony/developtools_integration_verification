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
import enum
import logging
import os
import sys
from subprocess import Popen, PIPE, STDOUT

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep)
from config import *

log_tag = 'utils'


class AclCheckException(Exception):
    def __init__(self, msg):
        self.msg = msg


def timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


class LogLevel(enum.Enum):
    Error = 1
    Info = 2


logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %a')


def log(msg):
    logging.error(msg)


def set_log_content(level, tag, msg):
    log_content = timestamp() + ' {}'.format(level) + ' [{}]'.format(tag) + ' {}'.format(msg)
    print(log_content)
    log(log_content)
    return (log_content)


def shell_command(command_list: list):
    try:
        print(command_list)
        process = Popen(command_list, stdout=PIPE, stderr=STDOUT)
        exitcode = process.wait()
        set_log_content(LogLevel(2).name, log_tag, '{} operation fuccessful!'.format(command_list))
        return process, exitcode
    except Exception as e:
        set_log_content(LogLevel(1).name, log_tag, e.msg)
        raise AclCheckException(e.msg)


def hdc_command(command):
    print(command)
    command_list = command.split(' ')
    _, exitcode = shell_command(command_list)
    return exitcode
