#! /usr/bin/env python
#coding=utf-8

from .napi_rule import NapiRule
from .sa_rule import SaRule

def check_all_rules(mgr, args):
	rules = [
		NapiRule,
		SaRule
	]

	passed = True
	for rule in rules:
		r = rule(mgr, args)
		if not r.check():
			passed = False

		if not passed:
			r.log("  Please refer to: \033[91m%s\x1b[0m" % r.get_help_url())

	if args and args.no_fail:
		return True

	return passed
