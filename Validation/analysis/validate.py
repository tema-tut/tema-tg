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

from sys import argv,exit
import optparse
from time import sleep

from tema.validator.modelvalidator import *
from tema.model import getModelType,loadModel

def validateModel(modelName,modelFormat,modelType):
    
    if not modelFormat:
        modelFormat = getModelType(modelName)        
        
    if modelType:
        modelType = eval("ModelValidator.%s" % modelType.upper())
    else:
        modelFormats = [ "mdm","lsts" ]
        for format in modelFormats:
            if modelName.endswith(".refined.%s" % format ):
                modelType = ModelValidator.REFINED_MACHINE
            elif modelName.endswith("-im.%s" % format ):
                modelType = ModelValidator.INITIALIZATION_MACHINE
            elif modelName.endswith("-lm.%s" % format ):
                modelType = ModelValidator.LAUNCH_MACHINE
            elif modelName.endswith("-rm.%s" % format ):
                modelType = ModelValidator.REFINEMENT_MACHINE
            elif modelName.endswith(".%s" % format ):
                modelType = ModelValidator.ACTION_MACHINE
            elif modelName.endswith(".ext") or modelName.endswith(".parallellsts") or modelName.endswith(".parallel"):
                modelType = ModelValidator.COMPOSED_MACHINE

            if modelType is not None:
                break
        else:
            print 'File %s is in unknown format' % modelName
            print ''
            return

    model = None
    if modelName == "-":
        modelFile = sys.stdin
    else:
        modelFile = open(modelName)
    try:
        model = loadModel(modelFormat,modelFile)
    finally:
        if modelName != "-":
            modelFile.close()
                
    errors = []
    warnings = []

    validator = ModelValidator(model)

    lock = validator.beginValidation(modelType, errors, warnings)
    if lock == None:
        print 'Model %s is of an unknown type.' % modelName
        print ''
        return

    while True:
        sleep(0.1)
        if not lock.locked():
            break

    pruneErrors(errors)
    pruneErrors(warnings)
    for i in errors + warnings:
        for j in i[1]:
            if j[:4] == 'path' and i[1][j] != None:
                i[1][j] = [str(k) for k in i[1][j]]

    if (len(errors) == 0 and len(warnings) == 0):
        print 'Model %s is valid.' % modelName
    else:
        if (len(errors) > 0):
            print 'Errors in model %s:\n' % modelName +\
                str([(i[0], ModelValidator.defaultErrorMessages[i[0]] % i[1]) for i in errors])
        if (len(warnings) > 0):
            print 'Warnings in model %s:\n' % modelName +\
                str([(i[0], ModelValidator.defaultErrorMessages[i[0]] % i[1]) for i in warnings])
    print ''

def readArgs():

    usagemessage = "usage: %prog [options] [filenames]"
    description = "If no filenames are given or filename is -, reads from standard input"
    parser = optparse.OptionParser(usage=usagemessage,description=description)
    
    parser.add_option("-f", "--format", action="store", type="str",
                      help="Format of the model file")

    parser.add_option("-t", "--type", action="store", type="str",
                      help="Type of the model")

    options, args = parser.parse_args(argv[1:])

    if len(args) == 0:
        args.append("-")
    elif "-" in args and len(args) > 1:
        parser.error("Can't read from stdin and from files at the same time")

    if not options.format and "-" in args:
        parser.error("Reading from standard input requires format parameter")
    if options.type and options.type.upper() not in ["REFINED_MACHINE","INITIALIZATION_MACHINE","LAUNCH_MACHINE","REFINEMENT_MACHINE","ACTION_MACHINE","COMPOSED_MACHINE"]:
        parser.error("Unknown model type '%s'" % options.type)
    return args,options


def main():
    args,options = readArgs()
    print ''
    for filename in args:
        validateModel(filename,options.format,options.type)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(1)
