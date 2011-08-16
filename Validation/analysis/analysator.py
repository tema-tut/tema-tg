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
Analyses test models, gives numerical information about their reachable portion and an estimate about the same information for their composition. All estimates are upper bounds.
"""

import os
import sys
import optparse

import tema.model.model
from tema.model import getModelType,loadModel

ACTIONS = 'actions'
ACTIONWORDS = 'action words'
STATES = 'states'
SLEEPSTATES = 'sleep states'
TRANSITIONS = 'transitions'
STATEPROPOSITIONS = 'state propositions'
STATEPROPOSITION_COMBINATIONS = 'state proposition combinations'
SLEEPING_STATEPROPOSITION_COMBINATIONS = 'sleeping state proposition combinations'
ACTIONWORD_STATEPROPOSITION_COMBINATIONS = 'action word - state proposition combinations'

ORDER = [ACTIONS, ACTIONWORDS, STATES, SLEEPSTATES, TRANSITIONS, STATEPROPOSITIONS, STATEPROPOSITION_COMBINATIONS, SLEEPING_STATEPROPOSITION_COMBINATIONS, ACTIONWORD_STATEPROPOSITION_COMBINATIONS]

COMMONS_MULTITARGET  = {ACTIONS:0, ACTIONWORDS:0, STATES:1, TRANSITIONS:0, STATEPROPOSITIONS:1, STATEPROPOSITION_COMBINATIONS:2, ACTIONWORD_STATEPROPOSITION_COMBINATIONS:0}
COMMONS_SINGLETARGET = {ACTIONS:6, ACTIONWORDS:1, STATES:6, TRANSITIONS:6, STATEPROPOSITIONS:3, STATEPROPOSITION_COMBINATIONS:3, ACTIONWORD_STATEPROPOSITION_COMBINATIONS:1}

def analyseModel(model):
    for prop in model.getInitialState().getStateProps():
        if str(prop).endswith('SwitcherBase'):
            base_prop = prop
            break
    else:
        base_prop = None

    actions = set()
    states = set()
    sleepstates = set()
    transitions = set()
    stateprops = set()
    stateprop_combs = set()
    sleep_stateprop_combs = set()
    aw_stateprop_combs = set()

    def isSleepState():
        return base_prop in current_props

    def isActionWord(action):
        return str(action).find(':start_aw') != -1

    stack = [model.getInitialState()]
        
    while len(stack) > 0:
        state = stack.pop()
        current_props = frozenset(state.getStateProps())

        states.add(state)

        if isSleepState():
            sleepstates.add(state)

        for stateprop in current_props:
            stateprops.add(stateprop)

        stateprop_combs.add(current_props)

        if isSleepState():
            sleep_stateprop_combs.add(current_props)

        for transition in state.getOutTransitions():
            current_action = transition.getAction()

            actions.add(current_action)

            transitions.add(transition)

            if isActionWord(current_action):
                aw_stateprop_combs.add((current_action, current_props))

            if transition.getDestState() not in states:
                stack.append(transition.getDestState())

    result = {}
    result[ACTIONS] = len(actions)
    result[ACTIONWORDS] = len([a for a in actions if isActionWord(a)])
    result[STATES] = len(states)
    result[SLEEPSTATES] = len(sleepstates)
    result[TRANSITIONS] = len(transitions)
    result[STATEPROPOSITIONS] = len(stateprops)
    result[STATEPROPOSITION_COMBINATIONS] = len(stateprop_combs)
    result[SLEEPING_STATEPROPOSITION_COMBINATIONS] = len(sleep_stateprop_combs)
    result[ACTIONWORD_STATEPROPOSITION_COMBINATIONS] = len(aw_stateprop_combs)

    return result

def calculateTotalResults(modelresults, commons = COMMONS_MULTITARGET):
    totalresults = {SLEEPSTATES:1, SLEEPING_STATEPROPOSITION_COMBINATIONS:1}
    totalresults.update(commons)

    for result in modelresults:
        totalresults[SLEEPSTATES] *= result[SLEEPSTATES]
        totalresults[SLEEPING_STATEPROPOSITION_COMBINATIONS] *= result[SLEEPING_STATEPROPOSITION_COMBINATIONS]

    totalresults[STATES] *= totalresults[SLEEPSTATES]
    totalresults[TRANSITIONS] *= totalresults[SLEEPSTATES]
    totalresults[STATEPROPOSITION_COMBINATIONS] *= totalresults[SLEEPING_STATEPROPOSITION_COMBINATIONS]
    totalresults[ACTIONWORD_STATEPROPOSITION_COMBINATIONS] *= totalresults[SLEEPING_STATEPROPOSITION_COMBINATIONS]

    for result in modelresults:
        external_sleepstates = totalresults[SLEEPSTATES] / result[SLEEPSTATES]
        external_sleeppropcombinations = totalresults[SLEEPING_STATEPROPOSITION_COMBINATIONS] / result[SLEEPING_STATEPROPOSITION_COMBINATIONS]

        totalresults[ACTIONS] += result[ACTIONS] - commons[ACTIONS]
        totalresults[ACTIONWORDS] += result[ACTIONWORDS] - commons[ACTIONWORDS]
        totalresults[STATES] += (result[STATES] - result[SLEEPSTATES] * commons[STATES]) * external_sleepstates
        totalresults[TRANSITIONS] += (result[TRANSITIONS] - result[SLEEPSTATES] * commons[TRANSITIONS]) * external_sleepstates
        totalresults[STATEPROPOSITIONS] += result[STATEPROPOSITIONS] - commons[STATEPROPOSITIONS]
        totalresults[STATEPROPOSITION_COMBINATIONS] += (result[STATEPROPOSITION_COMBINATIONS] - result[SLEEPING_STATEPROPOSITION_COMBINATIONS] * commons[STATEPROPOSITION_COMBINATIONS]) * \
            external_sleeppropcombinations
        totalresults[ACTIONWORD_STATEPROPOSITION_COMBINATIONS] += (result[ACTIONWORD_STATEPROPOSITION_COMBINATIONS] - \
                                                                           result[SLEEPING_STATEPROPOSITION_COMBINATIONS] * commons[ACTIONWORD_STATEPROPOSITION_COMBINATIONS]) * \
                                                                           external_sleeppropcombinations

    return totalresults

def analyseModels(models, commons = COMMONS_MULTITARGET):
    modelresults = []
    for model in models:
        if isinstance(model, tema.model.model.Model):
            modelresults.append(analyseModel(model))
        else:
            modelresults.append(model)

    totalresults = calculateTotalResults(modelresults, commons)

    return (modelresults, totalresults)

def parseresult(string):
    result = {}

    for line in string.strip().split(os.linesep):
        i = line.rfind(':')
        if i != -1:
            try:
                result[line[:i].strip()] = int(line[i+1:])
            except ValueError:
                pass

    return result

def printresult(name, results):
    print name + ':'
    for id in ORDER: #results.keys():
        print id + ': ' + str(results[id])

def readArgs():
    usagemessage = "usage: %prog structure [options] [filenames]"
    description = "If no filenames are given or filename is -, reads from standard input.\nstructure=multi|single"

    parser = optparse.OptionParser(usage=usagemessage,description=description)

    parser.add_option("-f", "--format", action="store", type="str",
                      help="Format of the model file")

    options, args = parser.parse_args(sys.argv[1:])

    if len(args) > 0 and args[0] in ["multi","single"]:
        structure = args[0]
    else:
        parser.error("Unknown structure parameter")
    
    args = args[1:]

    if len(args) == 0:
        args.append("-")
    elif "-" in args and len(args) > 1:
        parser.error("Can't read from stdin and from files at the same time")

    if not options.format and "-" in args:
        parser.error("Reading from standard input requires format parameter")
    
    return structure,args,options



def main():
    structure,files,options = readArgs()

    commons = {'multi':COMMONS_MULTITARGET, 'single':COMMONS_SINGLETARGET}[structure]

    models = []
    for filename in files:
        if options.format:
            modelType = options.format
        else:
            modelType = getModelType(filename)
        if modelType is None and filename.endswith('.analysis'):
            file = open(filename)
            try:
                content = file.read()
            finally:
                file.close()
                models.append(parseresult(content))

        elif modelType is None:
            print >>sys.stderr, "%s: Error. Unknown model type. Specify model type using '-f'" % os.path.basename(sys.argv[0])
            sys.exit(1)
        else:
            model = None
            if filename == "-":
                file = sys.stdin
            else:
                file = open(filename)
            try:
                model = loadModel(modelType,file)
            finally:
                file.close()
            models.append(model)

    results = analyseModels(models, commons)

    print
    for nameresult in zip(files, results[0]):
        printresult(nameresult[0], nameresult[1])
        print

    printresult('Estimated total', results[1])
    print

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
