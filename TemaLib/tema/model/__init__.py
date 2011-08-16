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

This directory is just a package for easing importing TEMA Python modules.
Add .../Temalib/ to PYTHONPATH, and you can say

import tema.guidance.guidance
import tema.model.parallelmodel

...etc
"""

def loadModel(modeltypestr,file_object):
    module=__import__("tema.model." + modeltypestr,globals(),locals(),[""])
    model_object=module.Model()
    model_object.loadFromFile(file_object)
    return model_object

def getModelType(modelfile):
        if modelfile.endswith(".ext") or modelfile.endswith(".parallellsts") or  modelfile.endswith(".parallel"):
                return "parallellstsmodel"
        elif modelfile.endswith(".lsts"):
                return "lstsmodel"
        elif modelfile.endswith(".mdm"):
                return "mdmmodel"
        elif modelfile.endswith(".log"):
                return "tracelogmodel"
        else:
                return None
