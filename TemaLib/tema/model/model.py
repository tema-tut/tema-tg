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
This module introduces base classes for testmodels.
"""
import re
_kwsplit=re.compile('^([a-zA-Z0-9]+:)?(~)?((kw|vw).*)$')
_awsplit=re.compile('^([a-zA-Z0-9]+:)?(~)?((end_aw|aw).*)$')

def _separate(kw,splitter):
    """
    Returns string triplet: phone,negation (if any),keyword_w_args. If
    kw is not a keyword, returns '','',''.
    """
    matchobj=splitter.match(kw)
    if not matchobj:
        return None,None,None
    else:
        if matchobj.group(1): g1=matchobj.group(1)
        else: g1=''
        if matchobj.group(2): g2=matchobj.group(2)
        else: g2=''       
        return g1,g2,matchobj.group(3)

class StateProp(object):
    """
    Each StateProp object contains the information on a single state
    proposition, usually a unique identifier (statepropId) and a
    string (statepropName).
    """
    def __init__(self,statepropId,statepropName=None):
        self._id = statepropId
        if statepropName != None:
            self._statepropName = statepropName
        else:
            self._statepropName = str(self._id)

    def __hash__(self):
        return hash(self._id)

    def __str__(self):
        return self._statepropName

    def toString(self):
        return str(self)

    def __eq__(self,stateprop):
        # The following type comparison requires that a new style
        # class is used (inherited from the object).
        return type(self)==type(stateprop) and self._id==stateprop._id 

    def equals(self,stateprop):
        return self.__eq__(stateprop)
    

class Action:
    """
    Action class contains the id and the name of an action.
    """
    def __init__(self,actionId,actionName=None):
        self._id = actionId
        if actionName != None:
            self._actionName = actionName
            self._phone,self._neg,self._keyword=_separate(actionName,_kwsplit)
            if self._keyword==None:
                self._modelcomp,self._neg,self._aw=_separate(actionName,_awsplit)
        else:
            self._actionName = str(self._id)

    def __hash__(self):
        return hash(self._id)

    def __str__(self):
        return self._actionName

    def __eq__(self,action):
        try:
            return self._id==action._id
        except AttributeError,e:
            return False

    def toString(self):
        return str(self)

    def isKeyword(self):
        """
        The first two characters of the name of an action identifies
        whether or not the action is a keyword. Keywords are expected
        to begin with kw or vw, negated keywords begin with ~ (no
        other action name should begin with ~).
        """
        return self._keyword!=None

    def isNegative(self):
        if self._neg=='~' or self._neg==None and str(self)[0]=="~":
            return True
        else:
            return False

    def negate(self):
        """
        Returns string corresponding to the negated action name.
        For example:

        Bob:kwX    --negate-> Bob:~kwX
        Alice:~kwY --negate-> Alice:kwY
        ~end_awZ   --negate-> end_awZ
        """
        if self._keyword!=None:
            if self._neg=='':
                return "%s~%s" % (self._phone,self._keyword)
            elif self._neg=='~':
                return "%s%s" % (self._phone,self._keyword)
        elif self._aw!=None:
            if self._neg=='':
                return "%s~%s" % (self._modelcomp,self._aw)
            elif self._neg=='~':
                return "%s%s" % (self._modelcomp,self._aw)

    def equals(self,action):
        return self.__eq__(action)

class State:
    """
    State class contains the id of a state and can generate the
    transitions that leave the state.
    """
    def __init__(self,globalStateId,outTransitions):
        """outTransitions is a list of Transition objects"""
        self._id=globalStateId
        self._outTransitions=outTransitions
        
    def __str__(self):
        return str(self._id)

    def __hash__(self):
        return hash(self._id)

    def getOutTransitions(self):
        """Returns list of transitions that leaves the state."""
        return self._outTransitions
    
    def execAction(self,action):
        """Returns the destination state of the first transition that
        leaves this state and is labelled by the action. If there is
        no such transition, returns None."""
        for t in self.getOutTransitions():
            if action.equals( t.getAction() ):
                return t.getDestState()
        return None

    def __eq__(self, other):
        try:
            return self._id==other._id
        except AttributeError,e:
            return False

    def equals(self, other):
        return self.__eq__(other)


class Transition:
    def __init__(self,sourceState,action,destState):
        self._sourceState=sourceState
        self._action=action
        self._destState=destState

    def __hash__(self):
        # some subclasses of State may have a list as their _id.
        # that's why the commented line below fails. (can't hash a list)
        #return hash((self._sourceState._id,self._action._id,self._destState._id))
        return hash((hash(self._sourceState),
                     hash(self._action),
                     hash(self._destState)))

    def __eq__(self,other):
        try:
            return self._sourceState == other._sourceState and \
                self._action == other._action and \
                self._destState == other._destState
        except AttributeError,e:
            return False

    def __str__(self):
        return "(%s,%s,%s)" % (self._sourceState,self._action,self._destState)
        
    def getAction(self): return self._action

    def getSourceState(self): return self._sourceState

    def getDestState(self): return self._destState

    def equals(self,transition):
        return self.__eq__(transition)

class Model:
    """
    Model is abstract base class for models. The point here is to show
    which methods should be implemented to a model. One load method is
    enough.
    """
    def __init__(self):
        pass

    def clearCache(self, *a, **kw):
        pass

    def loadFromObject(self,input_object):
        raise NotImplementedError()

    def loadFromFile(self,file_like_object):
        raise NotImplementedError()

    def getInitialState(self):
        """
        Returns a State object
        """
        raise NotImplementedError()

    def getActions(self):
        """
        Returns list of Action objects
        """
        raise NotImplementedError()

    def matchedActions(self, rex_set):
        rval= set()
        for a_name in [ alpha.toString() for alpha in self.getActions() ] :
            for rex in rex_set:
                if rex.match(a_name):
                    rval.add(a_name)
                    break
        return rval
