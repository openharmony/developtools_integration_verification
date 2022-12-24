#! /usr/bin/env python
#coding=utf-8

import os

class HdiParser(object):
	@staticmethod
	def load(mgr, product_out_path):
		# Decode hcb file to get hcs file
		hdi_tool = os.path.join(product_out_path, "obj/drivers/hdf_core/framework/tools/hc-gen/hc-gen")
		hcs_file = os.path.join(product_out_path, "packages/phone/vendor/etc/hdfconfig/hdf_default.hcb")
		out_file = os.path.join(product_out_path, "device_info.hcs")
		os.system('%s -d "%s" -o "%s"' % (hdi_tool, hcs_file, out_file))

		try:
			with open(out_file) as f:
				lines = f.readlines()
		except:
			try:
				out_file = os.path.join(product_out_path, "device_info.d.hcs")
				with open(out_file) as f:
					lines = f.readlines()
			except:
				return

		modules = []
		for line in lines:
			line = line.strip()
			if line.find("moduleName") < 0:
				continue
			parts = line.split("=")
			parts = [p.strip() for p in parts]
			if len(parts) < 2:
				continue
			name = parts[1]
			if name.endswith(";"):
				name = name[:-1]
			name=name.strip('"')
			name=name.strip("'")
			if name == "":
				continue

			if not name.endswith(".so"):
				name = "lib%s.z.so" % name
			modules.append(name)

		if not mgr:
			return

		for elf in mgr.get_all():
			if elf["name"] in modules:
				elf["hdiType"] = "hdi_service"

if __name__ == "__main__":
	parser = HdiParser()
	parser.load(None, "/home/z00325844/ohos/vendor/hihope/rk3568/hdf_config/uhdf/device_info.hcs")
