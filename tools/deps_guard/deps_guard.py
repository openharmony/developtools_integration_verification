#!/usr/bin/env python
#coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

from elf_file_mgr import ElfFileMgr

def __createArgParser():
	import argparse

	parser = argparse.ArgumentParser(description='Check architecture information from compiled output files.')

	parser.add_argument('-i', '--input',
						help='input asset files root directory', required=True)

	parser.add_argument('-r', '--rules', action='append',
						help='rules directory', required=False)

	parser.add_argument('-n', '--no-fail',
						help='force to pass all rules', required=False)

	return parser

def deps_guard(out_path, args=None):
	mgr = ElfFileMgr(out_path)
	mgr.scan_all_files()

	from rules_checker import check_all_rules

	passed = check_all_rules(mgr, args)
	if passed:
		print("All rules passed")
		return

	raise Exception("ERROR: deps_guard failed.")

if __name__ == '__main__':

	parser = __createArgParser()
	args = parser.parse_args()

	deps_guard(args.input, args)
