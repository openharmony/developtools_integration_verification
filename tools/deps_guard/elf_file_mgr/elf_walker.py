#! /usr/bin/env python
#coding=utf-8

import string
import json
import sys
import os
import struct

# find out/rk3568/packages/phone/system/ -type f -print | file -f - | grep ELF | cut -d":" -f1 | wc -l

class ELFWalker():
	def __init__(self, product_out_path="/home/z00325844/demo/archinfo/assets/rk3568/3.2.7.5"):
		self._files = []
		self._links = {}
		self._walked = False
		self._product_out_path = product_out_path

	def get_product_images_path(self):
		return os.path.join(self._product_out_path, "packages/phone/")

	def get_product_out_path(self):
		return self._product_out_path

	def __walk_path(self, subdir):
		for root, subdirs, files in os.walk(os.path.join(self._product_out_path, subdir)):
			for _filename in files:
				_assetFile = os.path.join(root, _filename)
				if os.path.islink(_assetFile):
					if _assetFile.find(".so") > 0:
						target = os.readlink(_assetFile)
						self._links[_assetFile] = target
					continue
				if not os.path.isfile(_assetFile):
					continue
				with open(_assetFile, "rb") as f:
					data = f.read(4)
					try:
						magic = struct.unpack("Bccc", data)
						if magic[0] == 0x7F and magic[1] == b'E' and magic[2] == b'L' and magic[3] == b'F':
							self._files.append(_assetFile)
					except:
						pass

		self._walked = True

	def get_link_file_map(self):
		if not self._walked:
			self.__walk_path("packages/phone/system")
			self.__walk_path("packages/phone/vendor")
		return self._links

	def get_elf_files(self):
		if not self._walked:
			self.__walk_path("packages/phone/system")
			self.__walk_path("packages/phone/vendor")
		return self._files

if __name__ == '__main__':
	elfFiles = ELFWalker()
	for f in elfFiles.get_elf_files():
		print(f)
	for src, target in elfFiles.get_link_file_map().items():
		print(src + " -> " + target)
