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

class CompileInfoLoader(object):
	@staticmethod
	def __load_output_module_info(product_out_path):
		try:
			with open(os.path.join(product_out_path, "packages/phone/system_module_info.json")) as f:
				modules = json.load(f)
		except:
			print("file info not found.")
			return None

		res = []
		for item in modules:
			info = {}
			info["name"] = item["dest"][0]
			if info["name"].startswith("updater/"):
				if len(item["dest"]) > 1:
					info["name"] = item["dest"][1]
				else:
					continue

			if "label" in item:
				info["labelPath"] = item["label"]
			else:
				info["labelPath"] = ""
			if info["labelPath"].find("(") > 0:
				info["labelPath"] = info["labelPath"][:info["labelPath"].find("(")]
			if "subsystem_name" in item:
				info["subsystem"] = item["subsystem_name"]
			else:
				if info["labelPath"].startswith("//build/common"):
					info["subsystem"] = "commonlibrary"
				else:
					info["subsystem"] = "unknown"
			if "part_name" in item:
				info["componentName"] = item["part_name"]
			else:
				if info["labelPath"].startswith("//build/common"):
					info["componentName"] = "c_utils"
				else:
					info["componentName"] = "unknown"
			if "label_name" in item:
				info["moduleName"] = item["label_name"]
			else:
				info["moduleName"] = ""
			if "version_script" in item:
				info["version_script"] = item["version_script"]
			info["third_party"] = False
			info["chipset"] = False
			info["napi"] = False
			info["innerapi"] = False
			info["innerapi_declared"] = False
			if "shlib_type" in item:
				info["shlib_type"] = item["shlib_type"]
			if "innerapi_tags" in item:
				info["innerapi_tags"] = item["innerapi_tags"]
			info["sa_id"] = 0
			res.append(info)
		return res

	@staticmethod
	def load(mgr, product_out_path):
		info = CompileInfoLoader.__load_output_module_info(product_out_path)

		defaultInfo = {
			"subsystem": "unknown",
			"componentName": "unknown",
			"moduleName": "unknown",
			"third_party": False,
			"chipset": False,
			"napi": False,
			"sa_id": 0,
			"labelPath": "",
			"version_script": "",
			"shlib_type": "",
			"innerapi": False,
			"innerapi_tags": [],
			"innerapi_declared": False
		}

		if info:
			for item in info:
				elf = mgr.get_elf_by_path(item["name"])
				if not elf:
					continue
				for k in defaultInfo.keys():
					if k in item:
						elf[k] = item[k]

		unknown_items = []
		for elf in mgr.get_all():
			if "componentName" not in elf:
				print("%s does not match in module info file" % (elf["path"]))
				unknown = defaultInfo.copy()
				unknown["name"] = elf["path"]
				unknown["fileName"] = elf["name"]
				for k in defaultInfo.keys():
					elf[k] = defaultInfo[k]
				unknown_items.append(unknown)
			elif elf["componentName"] == "unknown":
				print("%s has no componentName info" % (elf["path"]))
				unknown = defaultInfo.copy()
				unknown["name"] = elf["path"]
				for k in defaultInfo.keys():
					if k in elf:
						defaultInfo[k] = elf[k]
				unknown_items.append(unknown)

			if elf["path"].startswith("system/lib64/module/") or elf["path"].startswith("system/lib/module/"):
				elf["napi"] = True

			if not elf["path"].startswith("system/"):
				elf["chipset"] = True

			# Add if not exists
			if "shlib_type" not in elf:
				elf["shlib_type"] = ""
			if "innerapi_tags" not in elf:
				elf["innerapi_tags"] = []
			if elf["labelPath"].startswith("//third_party/"):
				elf["third_party"] = True

		if len(unknown_items) > 0:
			print("%d modules has no component info" % len(unknown_items))
			with open(os.path.join(product_out_path, "unknown.json"), "w") as f:
				res = json.dumps(unknown_items, indent=4)
				f.write(res)

		# init platformsdk, chipsetsdk, innerapi flags
		for elf in mgr.get_all():
			elf["deps_internal"] = []
			elf["deps_external"] = []
			elf["dependedBy_internal"] = []
			elf["dependedBy_external"] = []

			elf["modGroup"] = "private"
			elf["platformsdk"] = False
			elf["chipsetsdk"] = False

			elf["hdiType"] = ""
			if elf["shlib_type"] == "hdi_proxy":
				elf["hdiType"] = "hdi_proxy" # HDI proxy client library
			elif elf["shlib_type"] == "hdi_stub":
				elf["hdiType"] = "hdi_stub" # HDI proxy client library

			if elf["name"] in ("libc.so", "libc++.so", "libhilog.so"):
				elf["innerapi"] = True

			# Highest priority
			if elf["napi"]:
				elf["modGroup"] = "publicapi"

			if elf["sa_id"] > 0 or elf["type"] == "bin":
				elf["modGroup"] = "pentry"

		# for component dependedBy_internal and dependedBy_external

		platformsdks = []
		chipsetsdks = []
		innerapi_ccs = []

		for dep in mgr.get_all_deps():
			caller = dep["caller"]
			callee = dep["callee"]

			dep["platformsdk"] = False
			dep["chipsetsdk"] = False
			dep["external"] = False

			# For Inner API modules detection
			if caller["componentName"] == callee["componentName"]:
				caller["deps_internal"].append(dep)
				callee["dependedBy_internal"].append(dep)
			else:
				caller["deps_external"].append(dep)
				callee["dependedBy_external"].append(dep)
				callee["innerapi"] = True
				dep["external"] = True

				callee["modGroup"] = "innerapi_cc" # Cross component

			if caller["napi"]:
				caller["modGroup"] = "publicapi"

				# For Platform SDK modules detection
				callee["modGroup"] = "innerapi_chc" # Cross high level component

				dep["platformsdk"] = True
				callee["platformsdk"] = True
				if callee not in platformsdks:
					platformsdks.append(callee)
			elif caller["chipset"] != callee["chipset"]:
				# For Chipset SDK modules detection
				if callee["modGroup"] not in ("publicapi", "pentry"):
					callee["modGroup"] = "innerapi_chc" # Cross high level component
				if callee["hdiType"] != "hdi_proxy": # hdi proxy modules can be called by both system and chipset
					dep["chipsetsdk"] = True
					callee["chipsetsdk"] = True
					if callee not in chipsetsdks:
						chipsetsdks.append(callee)
			elif dep["external"] == True:
				if callee not in innerapi_ccs:
					innerapi_ccs.append(callee)

			# Highest priority
			if caller["napi"]:
				caller["modGroup"] = "publicapi"
			if callee["napi"]:
				callee["modGroup"] = "publicapi"

			if caller["sa_id"] > 0 or caller["type"] == "bin":
				caller["modGroup"] = "pentry"
			if callee["sa_id"] > 0 or callee["type"] == "bin":
				callee["modGroup"] = "pentry"

if __name__ == "__main__":
	import sqlite3
	import elf_modules
	conn = sqlite3.connect("symdb.db")
	cursor = conn.cursor()

	mgr = elf_modules.ElfModuleMgr(cursor)
