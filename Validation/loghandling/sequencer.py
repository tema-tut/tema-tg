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

import time
import sys
import optparse

def readlog(aw_only,file_object):
    te_executes = "TestEngine: Executing: "
    actions = []

    for line in file_object:
        if te_executes in line:
                actions.append( line.split(te_executes)[1].strip() )
    actiontree = []
    for action in actions:
        if aw_only:
            if(action.find("start_aw") != -1 or action.find("start_sv") != -1):
                actiontree.append([action])
	    elif(action.find("end_aw") != -1 or action.find("end_sv") != -1):
                actiontree[-1].append(action)
        else:
	    if(action.find("end_aw") != -1 or action.find("end_sv") != -1 or action.find("kw_") != -1 or action.find("vw_") != -1):
                actiontree[-1].append(action)
	    else:
                actiontree.append([action])
    if aw_only:
        actiontree[-1].append(actiontree[-1][0].replace("start_", "end_", 1))
    length = 1
    sequences = []
    while length < len(actiontree):
        sequences.append(createSequence(actiontree, length))
        length = 2 * length
    if len(actiontree) > 0:
        sequences.append(createSequence(actiontree, len(actiontree)))
    print "   THEN   ".join(sequences).strip()
    #print "\n\n".join(sequences)
    
def createSequence(actiontree, length):
    actions = []
    for i in range(-length, 0):
        actions = actions + actiontree[i]
    return createTreeSequence(["action " + action for action in actions])
    #return "\n".join(actions)

def createTreeSequence(actionList):
    length = len(actionList)
    if length == 1:
        return actionList[0]
    else:
        return '(' + createTreeSequence(actionList[:length/2]) + ' THEN ' + createTreeSequence(actionList[length/2:]) + ')'

def readArgs(argv):
    usagemessage = "usage: %prog [logfilename] [options]"
    description = "If no filename is given or filename is -, reads from standard input"

    parser = optparse.OptionParser(usage=usagemessage,description=description)
    parser.add_option( "--aw-only", action="store_true",default=False,
                      help="Sequence only action words")

    options,args = parser.parse_args(argv)

    if len(args) == 0:
        logfile = "-"
    elif len(args) == 1:
        logfile = args[0]

    return options,logfile

def main():
    options,logfile = readArgs(sys.argv[1:])
    if logfile == "-":
        logobject = sys.stdin
    else:
        logobject = open(logfile,'r')
    try:
        try:
            readlog(options.aw_only,logobject)
        except KeyboardInterrupt:
            pass
    finally:
        if logfile != "-":
            logobject.close()

if __name__ == '__main__':
    main()
