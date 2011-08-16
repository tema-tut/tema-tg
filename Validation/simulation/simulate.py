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
Simulates test model
"""

import sys
import copy
import os
import optparse
from tema.model import getModelType,loadModel

def load_testdata(testdata_args):
    module=__import__("tema.data.testdata",globals(),locals(),[""])
    testdata=module.TestData()
    # assuming that testdata_args are of form key:value,key2:value2,...
    # see set_parameters function in testengine to do this properly
    for key,value in [kv.split(":") for kv in testdata_args.split(",")]:
        testdata.setParameter(key,value)
    testdata.prepareForRun()
    return testdata

def simulate(starting_state,testdata):

    state=starting_state
    stack=[]
    action=""
    while action!="q":
        outtrans=state.getOutTransitions()
        print ""
        for i,t in enumerate(outtrans):
            print "%3i: %30s -> %s" % (i+1,t.getAction(),t.getDestState())
        action=raw_input("(%s) -> " % state)
        try:
            chosen=int(action)-1
            if testdata:
                stack.append((state,copy.deepcopy(testdata._runtimedata.namespace)))
            else:
                stack.append(state)
            state=outtrans[chosen].getDestState()
            if testdata:
                try: paction=testdata.processAction(str(outtrans[chosen].getAction()))
                except Exception, e:
                    print "error in execution:",e
                else: print "executed: '%s'" % paction
        except:
            if action=="b":
                if stack:
                    if testdata:
                        state,testdata._runtimedata.namespace=stack.pop()
                    else:
                        state=stack.pop()
                else: print "Already in the initial state"
            elif action=="i": state=starting_state

def readArgs():

    usagemessage = "usage: %prog [filename] [options]"
    description = "If no filename is given or filename is -, reads from standard input"
    parser = optparse.OptionParser(usage=usagemessage,description=description)

    parser.add_option("-f", "--format", action="store", type="str",
                      help="Format of the model file")

    parser.add_option("--testdata", action="store", type="str",
                      help="Testdata for model")

    options, args = parser.parse_args(sys.argv[1:])

    if len(args) == 0:
        modelfile = "-"
    elif len(args) == 1:
        modelfile = args[0]
    else:
        parser.error("More than one filename given")

    if not options.format and modelfile == "-":
        parser.error("Reading from standard input requires format parameter")
        

    return modelfile,options

def main():
    modelfile,options=readArgs()

    if options.testdata:
        testdata=load_testdata(options.testdata)
    else:
        testdata=None

    try:
        modeltype=options.format
        if not modeltype:
            modeltype = getModelType(modelfile)

        if not modeltype:
            print >>sys.stderr, "%s: Error. Unknown model type. Specify model type using '-f'" % os.path.basename(sys.argv[0])
            sys.exit(1)
            
        if modelfile == "-": 
            file_object=sys.stdin
        else:
            file_object=open(modelfile)

        m=loadModel(modeltype,file_object)
    except Exception,  e:
        print >>sys.stderr,e
        sys.exit(1)


    simulate(m.getInitialState(),testdata)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
