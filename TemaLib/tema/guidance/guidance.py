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
This file includes base classes for implementing different guidances.

Using Guidance interface:

1. give no arguments for constructor

2. call setTestModel(model_object)

3. call addRequirement(requirement) as many times as needed. Feel free
   to add fields like guidance_priority and guidance_skiphistory etc.
   to the requirements and implement a guidance that uses the fields.

4. call prepareForHistory() before starting to insert the history data.

5. call prepareForRun() before starting the action.


During the history load:

1. call markExecuted(transition_object) to mark the transition
   already executed before the actual test run.


During the test run:

1. call suggestAction(state_object) to get an action that the guidance
   would try to execute in the state state_id.

2. call markExecuted(transition_object) to tell the guidance
   which transition was actually executed.

"""
__docformat__ = "restructuredtext en"
version="0.1 guidance-base"

import tema.coverage.coverage as coverage
import tema.model.model as model

class Guidance:
    def __init__(self):
        self._requirements=[]
        self._testmodel=None
        self._working_mode="Initialize"
        self._params={}

    def log(self,*args): pass

    def setTestModel(self,model_object):
        if not isinstance(model_object,model.Model):
            raise TypeError("invalid model")
        self._testmodel=model_object

    def setParameter(self,parametername,parametervalue):
        """
        Sets parameters for guidance

        :Parameters:
            parametername : str
                Name of the parameter
            parametervalue : str
                Value of the parameter
        """
        self._params[parametername]=parametervalue

    def getParameter(self,parametername,defaultvalue=None):
        return self._params.get(parametername,defaultvalue)

    def getParameters(self):
        return self._params
    
    def addRequirement(self,requirement):
        if not self._testmodel:
            raise ValueError("test model is not set")
        if not isinstance(requirement,coverage.Requirement):
            raise TypeError("invalid requirement")
        self._requirements.append( requirement )

    def suggestAction(self,state_object):
        raise NotImplementedError()

    def markExecuted(self,transition_object):
        for r in self._requirements:
            r.markExecuted(transition_object)

    def prepareForHistory(self):
        pass

    def prepareForRun(self):
        self.log("Using parameters %s" % self.getParameters())

    def isThreadable(self):
        """Returns whether this guidance can be executed in a (non-main) thread.
        """
        # By default, yes.
        return True


# # The rest of the code would ensure that the methods in guidance
# # classes are executed in the correct order. However, due to Xerox
# # patent on Aspect Oriented Programming and our project rules, we had
# # to comment out this code and leave aspects module out of the
# # package.

# import aspects


# class ModeError(Exception): pass


# def _working_mode(accepted_modelist,new_mode,classmethod):
#     """
#     accepted_modelist = list of accepted working modes
#     new_mode = new mode or None for no change
#     """
#     def check_working_mode(self,*args):
#         """if called function did not throw exception,
#         assume that the mode can be changed"""
#         if not self._working_mode in accepted_modelist:
#             raise ModeError("allowed working modes %s, were in '%s'" %
#                             (accepted_modelist,self._working_mode))
#         try:
#             retval=self.__proceed(*args)
#         except Exception,e:
#             raise e
#         else:
#             if new_mode: self._working_mode=new_mode
#             return retval
#     # end check_working_mode
#     aspects.wrap_around(classmethod,check_working_mode)


# def _peel_methods(self,*args):
#     try:
#         retval=self.__proceed(*args)
#     except Exception,e:
#         raise e
#     else:
#         aspects.peel_around(Guidance.suggestAction)
#         aspects.peel_around(Guidance.markExecuted)
#         return retval


# _working_mode(["Initialize"],"Add reqs",Guidance.setTestModel)
# _working_mode(["Add reqs"],None,Guidance.addRequirement)
# _working_mode(["Add reqs"],"History",Guidance.prepareForHistory)
# _working_mode(["Add reqs","History"],"Run",Guidance.prepareForRun)
# _working_mode(["Run"],None,Guidance.suggestAction)
# _working_mode(["Run"],None,Guidance.markExecuted)

# aspects.wrap_around(Guidance.prepareForRun,_peel_methods)
