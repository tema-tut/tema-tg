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
Dummy coverage implements requirement interface but gives always zero
percentage. This can be used for test runs that should run without
stopping condition.
"""

# tema libraries:
import tema.coverage.coverage as coverage
# python standard
import re

class DummyCoverage(coverage.CoverageStorage, coverage.Requirement):

    def __init__(self, reqstr, **kw):
        # CoverageStorage constructor is skipped here
        # because there should be no need to use this as
        # a coverage storage. That is, this coverage should
        # not be used with guidance algorithms that calculate
        # forward. If it still is, a warning is given
        self._warning_given = 0
        
        if reqstr!="":
            self.log("WARNING: DummyCoverage got a non-empty coverage requirement: '%s'" % reqstr)
        self.log("Initialized")

    def setParameter(self, parametername, value ):
        print __doc__
        raise Exception("Invalid parameter '%s' for dummycoverage." % parametername)

    # CoverageStorage interface:
    def markExecuted(self,transition):
        # Mark execute is quite ok. We just do not care.
        pass

    def push(self):
        # Push and pop are bad. Someone is trying to see if
        # percentage gets better after a few steps. It won't,
        # because this gives always zero percentage. Therefore,
        # give warning.
        if self._warning_given == 0:
            self._warning_given = 1
            self.log("WARNING: DummyCoverage is used with too smart guidance algorithm.")
        
    def pop(self):
        # see push()
        self.push()

    # Requirement interface:
    
    def getPercentage(self):
        return 0.0

    def pickDataValue(self,set_of_possible_values):
        # This coverage requirement does not favor any particular data
        # values.
        return None

CoverageRequirement = DummyCoverage

