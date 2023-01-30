#! /usr/bin/env python
#coding=utf-8

import os
import json

class BaseRule(object):
	RULE_NAME = ""

	def __init__(self, mgr, args):
		self._mgr = mgr
		self._args = args
		self.__white_lists = self.load_files("whitelist.json")

	def load_files(self, name):
		rules_dir = []
		rules_dir.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../rules"))
		if self._args and self._args.rules:
			rules_dir = rules_dir + self._args.rules

		res = []
		for d in rules_dir:
			rules_file = os.path.join(d, self.__class__.RULE_NAME, name)
			try:
				with open(rules_file, "r") as f:
					jsonstr = "".join([ line.strip() for line in f if not line.strip().startswith("//") ])
					res = res + json.loads(jsonstr)
			except:
				pass

		return res

	def get_mgr(self):
		return self._mgr

	def get_white_lists(self):
		return self.__white_lists

	def log(self, info):
		print(info)

	def warn(self, info):
		print("\033[35m[WARNING]\x1b[0m: %s" % info)

	def error(self, info):
		print("\033[91m[NOT ALLOWED]\x1b[0m: %s" % info)

	def get_help_url(self):
		return "https://gitee.com/openharmony/developtools_integration_verification/tree/master/tools/deps_guard/rules/%s/README.md" % self.__class__.RULE_NAME

	# To be override
	def check(self):
		# Default pass
		return True
