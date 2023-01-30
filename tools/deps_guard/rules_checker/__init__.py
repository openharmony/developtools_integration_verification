#! /usr/bin/env python
#coding=utf-8

from .napi_rule import NapiRule
from .sa_rule import SaRule
from .hdi_rule import HdiRule
from .chipsetsdk import ChipsetSDKRule

def check_all_rules(mgr, args):
	rules = [
		NapiRule,
		SaRule,
		HdiRule,
		ChipsetSDKRule
	]

	passed = True
	for rule in rules:
		r = rule(mgr, args)
		r.log("Do %s rule checking now:" % rule.RULE_NAME)
		if not r.check():
			passed = False

		if not passed:
			r.log("  Please refer to: \033[91m%s\x1b[0m" % r.get_help_url())

	if args and args.no_fail:
		return True

	return passed
