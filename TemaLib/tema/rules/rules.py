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

class Rule:
    """
    Rule object holds actions and the resulting action of the
    synchronous execution of the actions. Types of the actions can be
    either unique identifiers (like unique integer id) or Action
    objects of model.py library (where __eq__ is implemented so that
    two actions are equal even if they are represented by two distinct
    objects --- this is needed when _enabled method is used).
    """
    
    def __init__(self,list_of_acts,resulting_act):
        """Initialise with list of actions that are executed
        synchronously and an action that is the result of the
        execution.
        """
        self.setSynchronousActions(list_of_acts)
        self.setResult(resulting_act)

    def __str__(self):
        return str(self.__syncacts)+" -> "+str(self.__result)

    def setSynchronousActions(self,list_of_acts):
        self.__syncacts=list_of_acts

    def setResult(self,resulting_act):
        self.__result=resulting_act
        
    def getSynchronousActions(self):
        return self.__syncacts

    def getResult(self):
        return self.__result
        
    def _enabled(self,list_of_acts):
        """Assume that every action in the list_of_acts can be
        executed. If the rule specifies a synchronous execution that
        can be applied in this situation (that is, self.__syncacts is
        a subset of list_of_acts), the function returns True. All
        indexes in the pair are global acts. Otherwise False is
        returned."""

        # Types of items in self.__syncacts and list_of_acts is
        # cruisal here! "(self.__syncacts[i] in list_of_acts)" must
        # work!

        for req_act in self.__syncacts:
            if not req_act in list_of_acts:
                return False
        return True


class RuleList(list):
    """List of Rule objects (do not use for any other datatype)"""

    def enabled(self,list_of_acts):
        """Returns the list of Rule-objects that are enabled when all
        actions in the list_of_acts can be executed."""
        return [ rule
                 for rule in list.__iter__(self)
                 if rule._enabled(list_of_acts)
                 ]

