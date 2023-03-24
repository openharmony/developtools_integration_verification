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

import os
import json

from .base_rule import BaseRule

class ChipsetSDKRule(BaseRule):
	RULE_NAME = "ChipsetSDK"

	def __is_chipsetsdk_tagged(self, mod):
		if not "innerapi_tags" in mod:
			return False
		if "ndk" in mod["innerapi_tags"]:
			return True
		if "chipsetsdk" in mod["innerapi_tags"]:
			return True
		return False

	def __write_innerkits_header_files(self, chipsetsdks):
		inner_kits_info = os.path.join(self.get_mgr().get_product_out_path(), "build_configs/parts_info/inner_kits_info.json")
		with open(inner_kits_info, "r") as f:
			info = json.load(f)

		headers = []
		for sdk in chipsetsdks:
			path = sdk["labelPath"][:sdk["labelPath"].find(":")]
			item = {"chipsetsdk": sdk["name"], "path": path, "headers": []}
			if sdk["componentName"] not in info:
				headers.append(item)
				continue

			for name, innerapi in info[sdk["componentName"]].items():
				if innerapi["label"] != sdk["labelPath"]:
					continue
				gotHeaders = True
				base = innerapi["header_base"]
				for f in innerapi["header_files"]:
					item["headers"].append(os.path.join(base, f))
			headers.append(item)

		try:
			with open(os.path.join(self.get_mgr().get_product_images_path(), "chipsetsdk_info.json"), "w") as f:
				json.dump(headers, f, indent = 4)
		except:
			pass

		return headers

	def __check_depends_on_chipsetsdk(self):
		lists = self.get_white_lists()

		passed = True

		chipsetsdks = []
		modules_with_chipsetsdk_tag = []

		# Check if any napi modules has dependedBy
		for mod in self.get_mgr().get_all():
			if self.__is_chipsetsdk_tagged(mod):
				modules_with_chipsetsdk_tag.append(mod)

			# Check chipset modules only
			if mod["path"].startswith("system"):
				continue

			# Check chipset modules depends
			for dep in mod["deps"]:
				callee = dep["callee"]

				# If callee is chipset module, it is OK
				if not callee["path"].startswith("system"):
					continue

				if callee not in chipsetsdks:
					if "hdiType" not in callee or callee["hdiType"] != "hdi_proxy":
						chipsetsdks.append(callee)
				# If callee is in Chipset SDK white list module, it is OK
				if callee["name"] in lists:
					continue

				# If callee is asan library, it is OK
				if callee["name"].endswith(".asan.so"):
					continue

				# If callee is hdi proxy module, it is OK
				if "hdiType" in callee and callee["hdiType"] == "hdi_proxy":
					continue

				# Not allowed
				passed = False
				self.error("chipset module %s depends on non Chipset SDK module %s in %s" % (mod["name"], callee["name"], mod["labelPath"]))

			# Check chipset modules dependedBy
			for dep in mod["dependedBy"]:
				caller = dep["caller"]

				# Called by chipset module, it is OK
				if not caller["path"].startswith("system"):
					continue

				if mod not in chipsetsdks:
					chipsetsdks.append(mod)

				# If chipset module is in Chipset SDK white list module, it is OK
				if mod["name"] in lists:
					continue

				# Not allowed
				passed = False
				self.error("system module %s depends on chipset module %s in %s" % (caller["name"], mod["name"], caller["labelPath"]))

		for mod in chipsetsdks:
			if not self.__is_chipsetsdk_tagged(mod):
				self.warn('Chipset SDK module %s has no innerapi_tags with "chipsetsdk" or "csdk", add it in %s' % (mod["name"], mod["labelPath"]))

		for mod in modules_with_chipsetsdk_tag:
			if mod["name"] not in lists:
				passed = False
				self.error('non chipsetsdk module %s with innerapi_tags="chipsetsdk" or "csdk", %s' % (mod["name"], mod["labelPath"]))

		self.__write_innerkits_header_files(chipsetsdks)

		return passed

	def check(self):
		return self.__check_depends_on_chipsetsdk()
