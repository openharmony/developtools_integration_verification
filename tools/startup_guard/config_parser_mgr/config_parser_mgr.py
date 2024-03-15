#!/usr/bin/env python
#coding=utf-8

#
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
#

import sys
sys.path.append('.')

from .param.system_parameter_parser import parameters_collect
from .cfg.config_parser import startup_config_collect

def __create_arg_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Check startup architecture information from compiled output files.')
    parser.add_argument('-i', '--input',
                        help='input config files base directory example "out/rk3568/packages/phone/" ', required=True)
    parser.add_argument('-c', '--target_cpu',
                    help='target_cpu cpu type" ', required=True)
    return parser

class ConfigParserMgr(object):
    def __init__(self, path = None):
        self._path = path
        self._parser_list = {}

    def load_all_parser(self, out_path, target_cpu):
        cfg_parser = startup_config_collect(out_path, target_cpu)
        param_parser = parameters_collect(out_path)
        self._parser_list = {'config_parser':cfg_parser, 'system_parameter_parser':param_parser}

    def get_parser_by_name(self, key):
        if key:
            return self._parser_list[key]

if __name__ == '__main__':
    args_parser = __create_arg_parser()
    options = args_parser.parse_args()
    mgr = ConfigParserMgr()
    mgr.load_all_parser(options.input, options.target_cpu)
