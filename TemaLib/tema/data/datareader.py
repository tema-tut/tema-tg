#!/usr/bin/env python
# Copyright (c) 2006-2010 Tampere University of Technology
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys

usage = """
datareader <datafilepath>

Example:
datareader datatable.td
"""

class ParseError(Exception):
	pass

def getDataInfo(contents):
	logicalname = contents.split(':',1)[0].split('(',1)[0].strip()

	i = 0
	while i < len(contents):
		for separator in ('"""', '"', "'"):
			if contents[i:i+len(separator)] == separator:
				j = i + len(separator) 
				while j < len(contents):
					if contents[j] == '\\':
						j = j+1
					elif contents[j:j+len(separator)] == separator:
						i = j + len(separator) - 1
						break
					j = j+1
				else:
					raise ParseError()
				break

		else:
			if contents[i] == '#':
				comment = contents[i+1:].strip()
				break

		i = i+1

	else:
		comment = ""

	return logicalname, comment


def main():
	if len(sys.argv) == 2:
		path = sys.argv[1]
		try:
			table = open(path, 'r')
		except IOError:
			print "Cannot open file '%s'" % path
			return
		try:
			contents = table.readline()
		finally:
			table.close()

		try:
			logicalname, comment = getDataInfo(contents)
		except ParseError:
			print "Cannot parse file '%s'" % path
			return

		print logicalname + '\n' + comment
	else:
		print usage

if __name__ == '__main__':
	main()
