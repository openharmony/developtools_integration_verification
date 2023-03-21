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

import string
import json
import sys
import os
import xml.etree.ElementTree as ET

def xml_node_find_by_name(node, name):
	for item in node:
		if item.tag == name:
			return item.text
	return None

class SAParser(object):
	@staticmethod
	def __parse_sa_profile(all_sa, f):
		root = ET.parse(f).getroot()
		process = xml_node_find_by_name(root, "process")
		for sa in root.findall("systemability"):
			libpath = xml_node_find_by_name(sa, "libpath")
			sa_key = os.path.basename(libpath)
			sa_item = {}
			for item in sa:
				sa_item[item.tag] = item.text
				sa_item["process"] = process
			all_sa[sa_key] = sa_item

	@staticmethod
	def __add_sa_info(all_sa, mgr):
		if not mgr:
			return
		for mod in mgr.get_all():
			mod["sa_id"] = 0
			if mod["name"] not in all_sa:
				continue
			mod["sa_id"] = int(all_sa[mod["name"]]["name"])

	@staticmethod
	def load(mgr, out_root_path):
		all_sa = {}
		path = os.path.join(out_root_path, "packages/phone/system/profile")
		if not os.path.exists(path):
			return

		for f in os.listdir(path):
			full_name = os.path.join(path, f)
			if os.path.isfile(full_name) and f.endswith(".xml"):
				try:
					SAParser.__parse_sa_profile(all_sa, full_name)
				except:
					pass

		SAParser.__add_sa_info(all_sa, mgr)
