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

import sys
import os
import tema.lsts.lsts as lsts
import tema.model.model as model

Action=model.Action

StateProp=model.StateProp

Transition=model.Transition

class State(model.State):
    """
    State class is redefined to support on-the-fly generation of the
    state space: not all State and Transition objects need to be
    generated at once. If outTransitions list is None and
    getOutTransitions method is called, the lsts model is asked to
    generate outTransitions for the state. The result is stored so
    next time the generation is not needed.
    """
    def __init__(self,globalStateId,outTransitions,lstsmodel=None):
        """outTransitions is a list of Transition objects"""
        model.State.__init__(self,globalStateId,outTransitions)
        self._model=lstsmodel

    def __str__(self):
        return str(self._id)
        
    def getOutTransitions(self):
        """Returns list of transitions that leaves the state."""
        if self._outTransitions==None:
            # If the out transitions were not already given, ask the
            # model to calculate them for us
            self._outTransitions=self._model._getOutTransitions(self._id)
        return self._outTransitions

    def getStateProps(self):
        """Returns list of state propositions with value true on the
        state (that is, associated to the state)"""
        return self._model._getStateProps(self._id)

class LstsModel(model.Model):
    def __init__(self,lstsobject=None):
        self._stateCache={}
        self._actionCache={}
        self._statepropCache={}
        if isinstance(lstsobject,lsts.lsts):
            self.loadFromObject(lstsobject)
        elif lstsobject != None:
            raise TypeError("the first constructor parameter should be an instance of lsts object")
        else:
            self._statepropnames=[]
        self._int2act=lambda i: self._lsts.get_actionnames()[i]
        self._int2sp=lambda i: self._statepropnames[i]

    def useActionMapper(self,actionmapper):
        """actionmapper implements functions int2act and act2int,
        which convert global action numbers to strings. Use this to
        get unique action names and numbers over LSTSs. LstsList can
        be used as an action mapper after executing createActionIndex.
        """
        self._int2act=actionmapper.int2act
        
    def loadFromObject(self,lsts_object):
        self._lsts=lsts_object
        self._statepropnames=self._lsts.get_stateprops().keys()
        self._statepropnames.sort()
        self._stateprops_by_state = None

    def loadFromFile(self,file_like_object):
        lsts_reader=lsts.reader()
        lsts_reader.read(file_like_object)
        self.loadFromObject(lsts_reader)

    def getInitialState(self):
        rv=self._newState(self._lsts.get_header().initial_states)
        return rv

    def getActions(self):
        return [ self._newAction(i) for i,a in enumerate(self._lsts.get_actionnames()) ]

    def getStatePropList(self):
        return [ self._newStateProp(i) for i,sp in enumerate(self._statepropnames) ]

    def _newState(self,stateid):
        if stateid in self._stateCache:
            return self._stateCache[stateid]
        else:
            s = State(stateid,None,self)
            self._stateCache[stateid] = s
            return s

    def _newAction(self,actionid):
        if actionid in self._actionCache:
            return self._actionCache[actionid]
        else:
            a = Action(actionid,self._int2act(actionid))
            self._actionCache[actionid] = a
            return a

    def _newStateProp(self,statepropid):
        if statepropid in self._statepropCache:
            return self._statepropCache[statepropid]
        else:
            sp = StateProp(statepropid,self._int2sp(statepropid))
            self._statepropCache[statepropid] = sp
            return sp

    def _getOutTransitions(self,state_id):
        """This method is called from a state object."""
        rv=[]
        outtrans=self._lsts.get_transitions()[ state_id ]
        for dest,act in outtrans:
            rv.append(
                Transition( self._newState(state_id),
                            self._newAction(act),
                            self._newState(dest) )
                )
        return rv

    def _getStateProps(self,state_id):
        """Returns the list of state proposition associated to the
        given state, This method is called from a state proposition
        object."""
        if self._stateprops_by_state == None:
            sp_by_st = lsts.props_by_states(self._lsts)
            self._stateprops_by_state = {}
            for st_id in range(len(sp_by_st)):
                if len(sp_by_st[st_id]) > 0:
                    self._stateprops_by_state[st_id] = [
                        self._newStateProp(sp_id)
                        for sp_id in sp_by_st[st_id]]
        return self._stateprops_by_state.get(state_id,[])

Model=LstsModel
