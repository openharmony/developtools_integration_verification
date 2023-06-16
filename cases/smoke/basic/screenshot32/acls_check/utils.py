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
