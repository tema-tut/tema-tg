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
"""
Usage: %s [target] < rules.ext > rules.ext.renamed

Renames rules files so that they are compatible with multitarget models.
"""

import sys
import re
import os

get_rule_number = re.compile(r'\(([0-9]+),"')
filename_re = re.compile(r'^([0-9]+)="((TargetSwitcher-rm)(\.lsts)|(.*?)(\.lsts\.nolayout|-awgt\.lsts))"')

def parse_args(argv):
    if len(argv) > 1:
        if argv[1] in ["-h","--help"]:
            print __doc__ % os.path.basename(sys.argv[0])
            sys.exit(1)
        target = argv[1]
    else:
        target = None
    return target

def rename_rules(target,input_fileobj,output_fileobj):
    contents = []
    transformations = {}
    # Find lines that are in format NUMBER="FILENAME.lsts", change them to 
    # format FILENAMEwEXT="FILENAME.lsts". If target given, prepend target to 
    # filename.
    for line in input_fileobj:
        m = filename_re.match(line)
        if m:
            if m.group(3) and m.group(4):
                filename = 3
                filetype = 4
            elif m.group(5) and m.group(6):
                filename = 5
                filetype = 6
            if target:
                line_transformed=filename_re.sub(r'%(target)s/\%(filename)d="%(target)s/\%(filename)d\%(filetype)d"' % {'target' : target,'filename':filename,'filetype':filetype},line)
                transformations[m.group(1)] = "%s/%s" % (target,m.group(filename))
            else:
                line_transformed=filename_re.sub(r'\%(filename)d="\%(filename)d\%(filetype)d"' % {'filename':filename,'filetype':filetype},line)
                transformations[m.group(1)] = m.group(filename)
        else:
            line_transformed = line

        contents.append(line_transformed)

    for line in contents:
        numbers = get_rule_number.findall(line)
        for number in numbers:
            transform = transformations[number]
            line = re.sub(r'\(%s,"' % number,r'(%s,"' %(transform),line)
        output_fileobj.write(line)

if __name__ == "__main__":
    # TODO: Better command line parameter handling
    # TODO: docstring
    target = parse_args(sys.argv)
    try:
        rename_rules(target,sys.stdin,sys.stdout)
    except KeyboardInterrupt:
        pass
