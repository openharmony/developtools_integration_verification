#! /usr/bin/env python
#coding=utf-8

import os
import sys
import string

DEBUG_NORMAL  = 1
DEBUG_VERBOSE = 2
DEBUG_SPAM	= 3

debuglevel = DEBUG_NORMAL

def debug(level, *msg):
	if debuglevel >= level:
		print(' '.join(msg))

# return a list of lines of output of the command
def command(command, *args):
	debug(DEBUG_SPAM, "calling", command, ' '.join(args))
	pipe = os.popen(command + ' ' + ' '.join(args), 'r')
	output = pipe.read().strip()
	status = pipe.close() 
	if status is not None and os.WEXITSTATUS(status) != 0:
		print("Command failed with status", os.WEXITSTATUS(status),  ":", \
			   command, ' '.join(args))
		print("With output:", output)
		sys.exit(1)
	return [i for i in output.split('\n') if i]
