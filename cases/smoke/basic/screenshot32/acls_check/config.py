import os
import platform
import time

# 系统分隔符
SYS_SEQ = os.sep
# 系统平台
SYS_PLATFORM = platform.system()

PATH = os.path.dirname(os.path.realpath(__file__)) + SYS_SEQ
# 脚本的执行日志
LOG_FILE = PATH + SYS_SEQ + "native_sa.log"
# 设备上生成的token info 文件名
TOKEN_INFO_NAME = 'token_info_{}.txt'.format(time.time_ns())
# 设备上生成文件存放位置
TOKEN_INFO_URL = '/data/{}'.format(TOKEN_INFO_NAME)
# 设备上文件生成命令
GENERATING_TOKEN_INFO_COMMAND = 'hdc shell atm dump -t > {}'.format(TOKEN_INFO_URL)
# 下载token info 文件存放路径
DOWNLOAD_TOKEN_INFO_URL = PATH + TOKEN_INFO_NAME
# 文件下载命令
DOWNLOAD_TOKEN_INFO_COMMAND = 'hdc file recv {} {}'.format(TOKEN_INFO_URL, DOWNLOAD_TOKEN_INFO_URL)
# 删除设备上的文件命令
CLEAR_TOKEN_INFO_FILE = 'hdc shell rm -rf {}'.format(TOKEN_INFO_URL)
