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

import os
import sys
import re
from optparse import OptionParser
_aw_re = re.compile('.* -> "(.*end_aw.*)"')
_kw_re = re.compile('.* -> "(~?[kv]w_.*)"')

def action_list(file_object):
    aws = set()
    kws = set()
    for line in file_object:
        if not line.startswith("#"):
            m = _aw_re.match(line)
            if m:
                aws.add(m.group(1))

            m = _kw_re.match(line)
            if m:
                kws.add(m.group(1))
    return sorted(list(aws)),sorted(list(kws))

def read_args(argv):
    usagemessage = "usage: %prog [rules_file] [options]\n\nIf no rules_file is given or rules_file is -, reads from standard input."
    description = "Lists all actions in a test model."

    parser = OptionParser(usage=usagemessage,description=description)
    parser.add_option( "--keywords", action="store_true",default=False,
                      help="List also keywords")
    parser.add_option( "-v", "--verbose", action="store_true",default=False,
                      help="Be more verbose")


    options,args = parser.parse_args(argv)

    if len(args) == 0:
        rules_file = "-"
    elif len(args) == 1:
        rules_file = args[0]
    else:
        parser.error("Can only read one rules file.")

    return options,rules_file


def _main(options,rules_file):
    aws = []
    kws = []
    if rules_file == "-":
        rules_input_file = sys.stdin
    else:
        rules_input_file = open(rules_file,'r')
    try:
        try:
            aws,kws = action_list(rules_input_file)
        except KeyboardInterrupt:
            pass
    finally:
        if rules_file != "-":
            rules_input_file.close()

    if options.verbose:
        print "Action words"
        print "------------"
    print os.linesep.join(aws)

    if options.verbose and options.keywords:
        print
        print "Keywords"
        print "--------"
        print os.linesep.join(kws)
    elif options.keywords:
        print 
        print os.linesep.join(kws)

if __name__ == "__main__":
    options,rules_file = read_args(sys.argv[1:])
    _main(options,rules_file)
