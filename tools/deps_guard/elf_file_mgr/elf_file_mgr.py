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
import sys
import os

from .elf_file import ElfFile
from .elf_walker import ELFWalker

class ElfFileWithDepsInfo(ElfFile):
	def __init__(self, file, prefix):
		super(ElfFileWithDepsInfo, self).__init__(file, prefix)
		self["deps"] = []
		self["dependedBy"] = []

	def __eq__(self, other):
		if not isinstance(other, ElfFileWithDepsInfo):
			return NotImplemented

		return self["id"] == other["id"]

	def dependsOn(self, mod):
		for dep in self["deps"]:
			if dep["callee"] == mod:
				return True
		return False

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return "%s:%d deps(%d) dependedBy(%d)" % (self["name"], self["id"], len(self["deps"]), len(self["dependedBy"]))

class Dependency(dict):
	def __init__(self, idx, caller, callee):
		self["id"] = idx
		self["caller_id"] = caller["id"]
		self["callee_id"] = callee["id"]
		self["caller"] = caller
		self["callee"] = callee
		self["external"] = False
		self["calls"] = 0

	def __eq__(self, other):
		if not isinstance(other, Dependency):
			return NotImplemented

		return self["id"] == other["id"]#and self["name"] == other["name"]

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return "(%s:%s[%d] -%d:%d-> %s:%s[%d])" % (self["caller"]["componentName"], self["caller"]["name"], self["caller"]["id"], int(self["external"]), self["calls"], self["callee"]["componentName"], self["callee"]["name"], self["callee"]["id"])

from .module_info import CompileInfoLoader
from .hdi import HdiParser
from .sa import SAParser
from .innerapi import InnerAPILoader

class ElfFileMgr(object):
	def __init__(self, product_out_path=None, elfFileClass=None, dependenceClass = None):
		self._elfFiles = []
		self._path_dict = {}
		self._basename_dict = {}
		if elfFileClass:
			self._elfFileClass = elfFileClass
		else:
			self._elfFileClass = ElfFileWithDepsInfo

		self._deps = []
		if dependenceClass:
			self._dependenceClass = dependenceClass
		else:
			self._dependenceClass = Dependency
		self._depIdx = 1
		self._elfIdx = 1

		self._not_found_depened_files = []

		walker = ELFWalker(product_out_path)
		self._prefix = walker.get_product_images_path()
		self._product_out_path = walker.get_product_out_path()
		self._link_file_map = walker.get_link_file_map()

	def scan_all_files(self):
		walker = ELFWalker(self._product_out_path)

		self._scan_all_elf_files(walker)
		self._build_deps_tree()

		self._maxDepth = 0
		self._maxTotalDepends = 0

		print("Load compile information now ...")
		CompileInfoLoader.load(self, self._product_out_path)
		HdiParser.load(self, self._product_out_path)
		SAParser.load(self, self._product_out_path)

	def get_product_images_path(self):
		return self._prefix

	def get_product_out_path(self):
		return self._product_out_path

	def add_elf_file(self, elf):
		# Append to array in order
		elf["id"] = self._elfIdx
		self._elfIdx = self._elfIdx + 1
		self._elfFiles.append(elf)

		# Add to dictionary with path as key
		self._path_dict[elf["path"]] = elf

		# Add to dictionary with basename as key
		if elf["name"] in self._basename_dict:
			self._basename_dict[elf["name"]].append(elf)
		else:
			self._basename_dict[elf["name"]] = [ elf ]

	def _scan_all_elf_files(self, walker):
		print("Scanning %d ELF files now ..." % len(walker.get_elf_files()))
		for f in walker.get_elf_files():
			elf = self._elfFileClass(f, self._prefix)
			if elf["path"] in self._path_dict:
				print("Warning: duplicate " + elf.get_file() + ' skipped.')
				continue

			# Ignore these files
			if elf["name"] in [ "ld-musl-aarch64.so.1", "ld-musl-arm.so.1", "hdc_std" ]:
				continue

			self.add_elf_file(elf)

		# Reorder libraries with same name as defined by LD_LIBRARY_PATH
		for bname, val in self._basename_dict.items():
			if len(val) < 2:
				continue
			self._basename_dict[bname] = self.__reorder_library(val)

	def __reorder_library(self, val):
		orders = []
		idx = 0
		for p in val:
			orders.append((self.__get_library_order(p["path"]), idx))
			idx = idx + 1
		orders.sort()

		res = []
		for item in orders:
			res.append(val[item[1]])

		return res

	def __get_library_order(self, path):
		if not path.startswith("/"):
			path = "/" + path
		if path.find("/lib64/") > 0:
			pathOrder = "/system/lib64:/vendor/lib64:/vendor/lib64/chipsetsdk:/system/lib64/ndk:/system/lib64/chipset-pub-sdk:/system/lib64/chipset-sdk:/system/lib64/platformsdk:/system/lib64/priv-platformsdk:/system/lib64/priv-module:/system/lib64/module:/system/lib64/module/data:/system/lib64/module/multimedia:/system/lib:/vendor/lib:/system/lib/ndk:/system/lib/chipset-pub-sdk:/system/lib/chipset-sdk:/system/lib/platformsdk:/system/lib/priv-platformsdk:/system/lib/priv-module:/system/lib/module:/system/lib/module/data:/system/lib/module/multimedia:/lib64:/lib:/usr/local/lib:/usr/lib"
		else:
			pathOrder = "/system/lib:/vendor/lib:/vendor/lib/chipsetsdk:/system/lib/ndk:/system/lib/chipset-pub-sdk:/system/lib/chipset-sdk:/system/lib/platformsdk:/system/lib/priv-platformsdk:/system/lib/priv-module:/system/lib/module:/system/lib/module/data:/system/lib/module/multimedia:/lib:/usr/local/lib:/usr/lib"

		if path.rfind("/") < 0:
			return 1000

		path = path[:path.rfind("/")]
		paths = pathOrder.split(':')
		idx = 0
		for p in paths:
			if p == path:
				return idx
			idx = idx + 1
		return 1000


	def _build_deps_tree(self):
		print("Build dependence tree for %d ELF files now ..." % len(self._elfFiles))
		for elf in self._elfFiles:
			self.__build_deps_tree_for_one_elf(elf)
		print("    Got %d dependencies" % self._depIdx)

	def add_dependence(self, caller, callee):
		dep = self._dependenceClass(self._depIdx, caller, callee)
		caller["deps"].append(dep)
		callee["dependedBy"].append(dep)

		self._deps.append(dep)
		self._depIdx = self._depIdx + 1
		return dep

	def __build_deps_tree_for_one_elf(self, elf):
		for lib in elf.library_depends():
			dep_elf = self.get_elf_by_name(lib)
			if not dep_elf:
				self._not_found_depened_files.append({"caller": elf["name"], "callee": lib})
				print("Warning: can not find depended library [" + lib + "] for " + elf["name"])
				break

			self.add_dependence(elf, dep_elf)

	def get_elf_by_path(self, path):
		if path not in self._path_dict and path.find("/lib64/") > 0:
			path = path.replace("/lib64/", "/lib/")
		if path in self._path_dict:
			return self._path_dict[path]
		if path.find("/platformsdk/") > 0:
			return None

		if path.startswith("system/lib64/"):
			path = path.replace("system/lib64/", "system/lib64/platformsdk/")
		elif path.startswith("system/lib/"):
			path = path.replace("system/lib/", "system/lib/platformsdk/")
		else:
			return None

		if path not in self._path_dict and path.find("/lib64/") > 0:
			path = path.replace("/lib64/", "/lib/")
		if path in self._path_dict:
			return self._path_dict[path]
		return None

	def get_elf_by_idx(self, idx):
		if idx < 1 or idx > len(self._elfFiles):
			return None
		return self._elfFiles[idx - 1]

	def __get_link_file(self, name):
		for src, target in self._link_file_map.items():
			tmp_name = os.path.basename(src)
			if name != tmp_name:
				continue
			tmp_name = os.path.dirname(src)
			tmp_name = os.path.join(tmp_name, target)
			link_elf = ElfFile(tmp_name, self._prefix)
			return self.get_elf_by_path(link_elf["path"])

	def get_elf_by_name(self, name):
		if name in self._basename_dict:
			return self._basename_dict[name][0]

		return self.__get_link_file(name)

	def get_all(self):
		return self._elfFiles

	def get_all_deps(self):
		return self._deps

if __name__ == '__main__':
	mgr = ElfFileMgr("/home/z00325844/demo/archinfo/assets/rk3568/3.2.7.5")
	mgr.scan_all_files()
	elf = mgr.get_elf_by_path("system/lib/libskia_ohos.z.so")
	print("Get skia now ...")

	res = mgr.get_elf_by_path("system/lib/platformsdk/libhmicui18n.z.so")
	print(res)
