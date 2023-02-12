#! /usr/bin/env python
#coding=utf-8

import os
import json

class InnerAPILoader(object):
	@staticmethod
	def load(mgr, product_out_path):
		print("Loading innerapis now ...")
		try:
			innerapis = InnerAPILoader.__load_innerapi_modules(product_out_path)
		except:
			innerapis = []

		if not mgr:
			return

		for elf in mgr.get_all():
			if elf["labelPath"] in innerapis:
				elf["innerapi_declared"] = True

	def __load_innerapi_modules(product_out_path):
		inner_kits_info = os.path.join(product_out_path, "build_configs/parts_info/inner_kits_info.json")
		with open(inner_kits_info, "r") as f:
			info = json.load(f)

		innerapis = []
		for name, component in info.items():
			for mod_name, innerapi in component.items():
				innerapis.append(innerapi["label"])

		return innerapis
