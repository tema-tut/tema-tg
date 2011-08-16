# coding: iso-8859-1
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
guiadapter let's the user decide (via ModelGui) whether
a positive or negative action is executed.
"""

# tema libraries:
import tema.adapter.adapter as adapter
AdapterError=adapter.AdapterError

from tema.validator.simulation.modelgui import getTheModelGui
from tema.model.parallellstsmodel import ParallelLstsModel as Model

class Adapter(adapter.Adapter):
    def __init__(self):
        adapter.Adapter.__init__(self)

    def setParameter(self,name,value):
        self.log("Parameter: %s: %s" % ( name, str(value) ) )
        if not name in self._allowed_parameters:
            print __doc__
            raise AdapterError("Illegal adapter parameter: '%s'." % name)
        adapter.Adapter.setParameter(self,name,value)

    def prepareForRun(self):
        pass

    def sendInput(self,actionname):
        if actionname.startswith("kw_IsTrue "):
            # the action is kw_IsTrue -> preventing the user to 
            # give the wrong answer.
            positive = actionname.split(None,1)[1]=="True"
            if positive:
                return getTheModelGui().executePosOrNeg(actionname,neg=False)
            else:
                return getTheModelGui().executePosOrNeg(actionname,pos=False)
        return getTheModelGui().executePosOrNeg(actionname)

    def stop(self):
        #TODO: what?
        pass


