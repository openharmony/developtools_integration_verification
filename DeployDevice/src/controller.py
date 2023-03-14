#!/usr/bin/env python
# -*- coding: utf-8 -*-


###############################################################
###作者：王琦                                        ###########
###功能：框架入口                                     ###########
###创建日期：20200424                                ###########
###############################################################
###############################################################

import os
import sys
import argparse
from core.run import *
from aw.Common.Constant import CONSTANT
from util.log_info import logger

if __name__ == "__main__":
    
    param_file = sys.argv[1]

    #parm_file的文件格式如下：taskid.properity。必须是taskid命名的文件
    cust_steps = parseProperties(param_file)

    errcode = start(cust_steps)
    if errcode != 0:
       logger.printLog("执行失败：错误信息：" + CONSTANT.ENVERRMESSAGE)
    logger.printLog(errcode)
    os._exit(errcode)
        
