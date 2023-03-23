#! /usr/bin/env python
#coding=utf-8

import json

from .base_rule import BaseRule

class NapiRule(BaseRule):
	RULE_NAME = "NO-Depends-On-NAPI"

	def __check_depends_on_napi(self):
		lists = self.get_white_lists()

		passed = True

		# Check if any napi modules has dependedBy
		for mod in self.get_mgr().get_all():
			if not mod["napi"]:
				continue

			if len(mod["dependedBy"]) == 0:
				continue

			targetName = mod["labelPath"][mod["labelPath"].find(":")+1:]
			if targetName in lists:
				continue

			self.error("napi module %s depended by:" % mod["name"])
			for dep in mod["dependedBy"]:
				caller = dep["caller"]
				self.log("   module [%s] defined in [%s]" % (caller["name"], caller["labelPath"]))
			passed = False

		return passed

	def check(self):
		return self.__check_depends_on_napi()
