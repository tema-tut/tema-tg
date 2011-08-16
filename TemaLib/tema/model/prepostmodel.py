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
Process description in pre/post conditions. All methods that do not
begin with '_' are considered names of actions. Attributes of the
object define state.

class PROCESSNAME(mopel.PrePost):

    def __init__(self):
        self.state=1

    def ACTION_NAME(self):
        if GUARD: # evaluating GUARD should not change attributes
            yield # this transition is enabled
            BODY
            [ yield 'ACTIONARGS' ] # optional arguments for action

    def UserInterruption(self):
        if self.state in [1,2,5,6]:
            yield
            old_state=self.state
            self.state=3
            yield 'at state %s' % old_state

Action can be given some parameters by yielding a string after
BODY. The string is concatenated with the action name to form the
action with parameters.


# This is something which might need rethinking:

class PROCESSNAME(mopel.StateMachine):

    def __init__(self):
        self.actions=['A','B','C']
        self.initial_state=self.Start
        self.variable=42

    def Start(self):
        out=[('A', self.Start, mopel.change()),
             ('C', self.Start, mopel.change(self.variable,11))]
        if self.variable==42: out.append(
            ('B',self.End,mopel.change(self.variable,18)))
        return out

    def End(self):
        return [] # deadlock

"""

import types
import copy
import cPickle
from tema.model.model import Action, Transition

class PrePost(object): pass

class StateMachine(object): pass

class PrePostModel(object):
    def __init__(self,PrePostClass):
        self._m=PrePostClass()
        self._actions=[]
        self._actioncache={}
        for attr in dir(self._m):
            if type(getattr(self._m,attr))==types.MethodType and attr[:1]!="_":
                action=Action(len(self._actions),attr)
                self._actions.append(action)
                self._actioncache[attr]=action
        self._statecache={} # pickled prepostobjs mapped to prepoststates

    def getInitialState(self):
        return PrePostState(self._m,self)
        
    def getActions(self):
        return self._actions

class PrePostState(object):
    next_id=0
    
    def __init__(self,prepostobj,prepostmodel):
        self._id=PrePostState.next_id
        PrePostState.next_id+=1
        self._state=prepostobj
        self._model=prepostmodel
        self._model._statecache[cPickle.dumps(self._state,2)]=self
        self._enabled_transitions=[]
        
    def getOutTransitions(self):
        if self._enabled_transitions: return self._enabled_transitions
        for action in self._model._actions:
            enabled=getattr(self._state,str(action))()
            try: enabled.next()# execute the guard
            except StopIteration: continue # it was false, take the next one
            
            orig=copy.deepcopy(self._state)
            try: action_args=enabled.next() # execute the body
            except StopIteration: pass
            else:
                new_action=str(action)+action_args
                try: action=self._model._actioncache[new_action]
                except KeyError:
                    action_id=len(self._model._actioncache)
                    action=Action(action_id,new_action)
                    self._model._actioncache[new_action]=action
            try: dest_state=self._model._statecache[cPickle.dumps(self._state,2)]
            except KeyError: dest_state=PrePostState(self._state,self._model)
            self._state=orig
            self._enabled_transitions.append(Transition(self,action,dest_state))
        return self._enabled_transitions

    def __str__(self):
        try: return self._str_repr
        except:
            self._str_repr=cPickle.dumps(self._state,2)
            return self._str_repr


class StateMachineModel(object):
    def __init__(self,StateMachineClass):
        self.m=StateMachineClass()

    def getInitialState(self):
        raise NotImplemented

    def getActions(self):
        return self.m.actions


class Model(object):
    def loadFromObject(self,cls):
        """cls is either of PrePost or StateMachine class"""
        if PrePost in cls.__bases__:
            self._ppm=PrePostModel(cls)
            self.getInitialState=self._ppm.getInitialState
            self.getActions=self._ppm.getActions
        elif StateMachine in cls.__bases__:
            self._smm=StateMachineModel(cls)
            self.getInitialState=self._smm.getInitialState
            self.getActions=self._smm.getActions
            
    def loadFromFile(self,fileobj):
        mod=__import__(fileobj.name[:-3],globals(),locals())
        for n in dir(mod):
            o=getattr(mod,n)
            if type(o) in [types.ClassType, types.TypeType] and \
               (PrePost in o.__bases__ or StateMachine in o.__bases__):
                self.loadFromObject(o)
                return
