# -*- coding: utf-8 -*-
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
trace_cov

Usage:
Either:
    --coverage=trace_cov --coveragereq="action A BLAA BLAA..."
Or:
    --coverage=trace_cov --coveragereq="" --coveragereq-args="file:blaafile.txt"
   where blaafile.txt contains the coveragereq.

"""


# python standard:
import re
# tema libraries:
import tema.coverage.coverage as coverage

skip_these_actions = [
    re.compile(r'kw_Delay.*') ]

def tarpeenton():
    for idx in xrange(0,len(self.__trace)):
        if idx >= len(self.__trace):
            break
        found = False
        for pattern in skip_these_actions:
            if pattern.match(self.__trace[idx]):
                found = True
                break
        if found:
            self.__trace[idx:idx+1]=[]


def _parseTrace(trace):
    __phase_1 = trace.strip().split(" THEN ")
    __phase_2 = [ re.sub(" *[(]*action ","", it) for it in __phase_1 ]
    __phase_3 = [ re.sub("[)]* *$", "", i) for i in __phase_2 ]
    return [ re.compile(i) for i in __phase_3 ]


class TraceCoverage(coverage.Requirement):
    def __init__(self, trace=None, model=None):
        if trace:
            self.__trace = _parseTrace(trace)
            if len(self.__trace) < 1 :
                raise Exception("Coverage:  Trace can not be empty")
        else:
            self.__trace = None
        self.__pointer_stack = [ 0 ]

    def setParameter(self, name, value):
        if name == 'file':
            if self.__trace:
                raise Exception("trace_cov needs either covearagereq string "\
                                "or a file parameter, NOT BOTH.")
            # let somebody else catch exceptions if file not found etc.
            reqFile = file( value, "r")
            reqStr = reqFile.read()
            reqFile.close()
            self.__trace = _parseTrace(reqStr)
        else:
            print __doc__
            raise Exception("Invalid param name for trace_cov: %s" % (name,))

    def markExecuted(self,transition):
        __idx = self.__pointer_stack[-1]
        if transition.getAction().toString() == self.__trace[__idx].pattern:
            __idx += 1
            self.__pointer_stack[-1] = __idx

    def getPercentage(self):
        __idx = self.__pointer_stack[-1]
        rval = float(__idx)/float(len(self.__trace))
        #self.log("Returning coverage_value: %.4f" % rval)
        return rval

    def getExecutionHint(self):
        __idx = self.__pointer_stack[-1]
        # self.log("DEBUG: mikähän olisi @"+self.__trace[__idx] + "@")
        #result = re.compile(self.__trace[__idx])
        result = self.__trace[__idx]
        # self.log("DEBUG: patterni " + result.pattern)
        return (set( [ result ] ), 1)


    def push(self):
        __idx = self.__pointer_stack[-1]
        self.__pointer_stack.append(__idx)

    def pop(self):
        self.__pointer_stack.pop()
        if not self.__pointer_stack:
            raise Exception("Superfluous 'pop' for coverage module")


requirement = TraceCoverage

