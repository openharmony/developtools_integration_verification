#! /usr/bin/env python
#coding=utf-8

from .napi_rule import NapiRule

def check_all_rules(mgr, args):
	passed = True
	napi = NapiRule(mgr, args)
	if not napi.check():
		passed = False

	if args and args.no_fail:
		return True

	return passed
