#! /usr/bin/env python
#coding=utf-8

from elf_file_mgr import ElfFileMgr

def createArgParser():
	import argparse

	parser = argparse.ArgumentParser(description='Check architecture information from compiled output files.')

	parser.add_argument('-i', '--input',
						help='input asset files root directory', required=True)

	parser.add_argument('-r', '--rules',
						help='rules directory', required=False)

	parser.add_argument('-n', '--no-fail',
						help='force to pass all rules', required=False)

	return parser

if __name__ == '__main__':

	parser = createArgParser()
	args = parser.parse_args()

	# Scan
	mgr = ElfFileMgr(args.input)
	mgr.scan_all_files()

	from rules_checker import check_all_rules
	check_all_rules(mgr, args)
