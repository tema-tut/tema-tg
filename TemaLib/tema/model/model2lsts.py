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
import os
import optparse

import tema.lsts.lsts as lsts
from tema.model import getModelType,loadModel


"""
Convert model file to lsts format
"""

help = """

Usage:

model2lsts [options] <filename>

Options:

-f <format>, --format <format>
        Specifies the model format of the file. If no format is specified, format is inferred from the file extension.

-o <filename>, --output <filename>
        Specifies the output file. If no file is specified, model will be printed into standard output.

Examples:

model2lsts model.mdm
model2lsts -f parallellsts -o rules.lsts rules.ext
"""

class ConversionModel(object):
    def __visit_state(self, state):
        if state not in self.__visitted:
            if len(self.__stateprops) > 0:
                for prop in state.getStateProps():
                    self.__stateprops[str(prop)].append(self.__next_state_num)
            self.__unexpanded.add(state)
            self.__visitted[state] = self.__next_state_num
            self.__next_state_num += 1
            self.__transitions.append([])

    def __init__(self, action_map, stateprops, init_state):
        self.__transitions = []
        self.__stateprops = dict()
        for prop in stateprops:
            self.__stateprops[prop] = []
        self.__visitted=dict()
        self.__unexpanded = set()
        self.__next_state_num = 0
        self.__visit_state(init_state)
        while self.__unexpanded:
            this = self.__unexpanded.pop()
            this_num = self.__visitted[this]
            for alpha, dest in [(a.getAction(), a.getDestState()) for a in this.getOutTransitions()]:
                self.__visit_state(dest)
                dest_num = self.__visitted[dest]
                alpha_num = action_map[str(alpha)]
                self.__transitions[this_num].append((dest_num, alpha_num))

    def getTransitions(self):
        return self.__transitions

    def getStateProps(self):
        return self.__stateprops

def convert_to_lsts(model, filelike_object):
    action_map = dict()
    visible_set = set([str(alpha) for alpha in model.getActions()])
    visible_set.discard("tau")
    action_vec = ["tau"] + [a for a in visible_set]
    for alpha, idx in zip(action_vec, xrange(len(action_vec))):
        action_map[alpha] = idx

    try:
        stateprops = [str(prop) for prop in model.getStatePropList()]
    except AttributeError:
        stateprops = []

    conversionmodel = ConversionModel(action_map, stateprops, model.getInitialState())

    w=lsts.writer(filelike_object)
    w.set_actionnames(action_vec)
    w.set_transitions(conversionmodel.getTransitions())
    w.set_stateprops(conversionmodel.getStateProps())
    w.write()

def convert(options, filename):

    format = options.format
    outputfilename = options.output

    if not format:
        format = getModelType(filename)
    if not format:
        print >>sys.stderr, "%s: Error. Unknown model type. Specify model type using '-f'" % os.path.basename(sys.argv[0])
        sys.exit(1)
    if filename == "-": 
        modelfile=sys.stdin
    else:
        modelfile=open(filename)
                
    model = None
    try:
        model = loadModel(format,modelfile)
    finally:
        modelfile.close()
                       
    if outputfilename != "-":
        out = open(outputfilename, 'w')
        try:
            convert_to_lsts(model, out)
        finally:
            out.close()
    else:
        convert_to_lsts(model, sys.stdout)

def readArgs():

    usagemessage = "usage: %prog [filename] [options]"
    description = "If no filename is given or filename is -, reads from standard input"

    parser = optparse.OptionParser(usage=usagemessage,description=description)
    
    parser.add_option("-f", "--format", action="store", type="str",
                      help="Format of the input model file")

    parser.add_option("-o", "--output", action="store", type="str", 
                      metavar="FILENAME", default="-",
                      help="Specifies the output file. If no file is specified or filename is '-', model will be printed into standard output.")

    options, args = parser.parse_args()

    if len(args) == 0:
        modelfile = "-"
    elif len(args) == 1:
        modelfile = args[0]
    else:
        parser.error("More than one filename given")

    if not options.format and modelfile == "-":
        parser.error("Reading from standard input requires format parameter")
        

    return modelfile,options

if __name__ == '__main__' or sys.argv[0]=="2lsts":
    inputfile,options = readArgs()
    convert(options,inputfile)
