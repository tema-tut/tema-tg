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
TestData

accepts arguments file:filename [file:filename...]
"""

# tema libraries:
import tema.data.dataimport as dataimport
# python standard:
import re

class ExpressionEvaluationError(Exception): pass

class TestData:

    def __init__(self):
        self._runtimedata=dataimport.RuntimeData()
        self._oldsyms={}
        # match data expressions in $(expr)$, where "$" cannot appear in expr
        self._dataregexp=r=re.compile('\$\(([^$]*)\)\$')
        self.log("Initialized, initial symbols: %s" % self._new_symbols())
        
    def _new_symbols(self):
        rv=", ".join( [s for s in self._runtimedata.namespace
                       if not s in self._oldsyms] )
        self._oldsyms.update(self._runtimedata.namespace)
        return rv
    
    def setParameter(self,name,value):
        if name=="file":
            try:
                self._runtimedata.loadFromFile(file(value))
            except Exception,msg:
                raise Exception("Failed to load file '%s': %s" % (value,msg))
            self.log("Loaded from '%s' symbols %s" % (value,self._new_symbols()))
        else:
            print __doc__
            raise Exception("Invalid parameter '%s' for TestData." % name)

    def prepareForRun(self):
        self.log("Ready to run with %s symbols." %
                 len(self._runtimedata.namespace))
        delattr(self,'_oldsyms')

    def processAction(self,actionstring):
        orig=actionstring
        m=self._dataregexp.search(actionstring)
        looplimit=100
        while m and looplimit>0:
            try:
                actionstring=actionstring[:m.start()] + \
                              self._runtimedata.evalString(m.group(1)) + \
                              actionstring[m.end():]
            except Exception,e:
                self.log("Runtime error when evaluating expression '%s' in '%s': %s" %
                         (m.group(1),orig,e))
                raise ExpressionEvaluationError(e)
            looplimit-=1
            m=self._dataregexp.search(actionstring)

        if looplimit==0:
            self.log("Runtime error: too long recursive evaluation in '%s'" % orig)
            return orig

        if actionstring!=orig:
            self.log("Converted: '%s' -> '%s'" % (orig,actionstring))
        return actionstring

    def log(*a): pass
