#! /usr/bin/env python
#coding=utf-8

import os
import json

class BaseRule(object):
	RULE_NAME = ""

	def __init__(self, mgr, args):
		self._mgr = mgr
		self.__load_white_lists(args)

	def __load_white_lists(self, args):
		res = []
		if args and args.rules:
			rules_path = args.rules
		else:
			rules_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../rules")

		rules_file = os.path.join(rules_path, self.__class__.RULE_NAME, "whitelist.json")
		with open(rules_file, "rb") as f:
			self.__white_lists = json.load(f)

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
