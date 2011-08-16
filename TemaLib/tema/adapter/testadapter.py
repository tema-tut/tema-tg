#!/usr/bin/env python
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
testadapter understands the following parameters:

- delay (float, default: 0.0)

  Delay between keyword executions

- model (string, default: '')

  Model to use for guidance. Model type can be given with notation 'file:type'

"""

# tema libraries:
import tema.adapter.adapter as adapter
AdapterError=adapter.AdapterError
from tema.model.model import Transition
from tema.model import getModelType,loadModel

# python standard:
import re
import random
import time

key_word_re = re.compile(r"~?kw_.*")
forsed_re=re.compile(r".*New.*Meeting.*")

class DelayedExecution:
    def __init__(self, adapter, sendInput, delay):
        self._adapter = adapter
        self._doKeyWord = sendInput
        self._delay = delay

    def __call__(self, action_name):
        retValue = self._doKeyWord(self._adapter, action_name)
        time.sleep(self._delay)
        return retValue


class Adapter(adapter.Adapter):
    def __init__(self):
        adapter.Adapter.__init__(self)
        self._is_running=False
        self._last_action_name=None
        self._last_action_cnt=0
        self._max_repetition=2
        self._allowed_parameters.append("model")
        self._allowed_parameters.append("delay")
        self._visible = False

    def setParameter(self,name,value):
        self.log("Parameter: %s: %s" % ( name, str(value) ) )
        if not name in self._allowed_parameters:
            print __doc__
            raise AdapterError("Illegal adapter parameter: '%s'." % name)
        if name == "model":
            param = value.split(":")
            model_file = param[0]
            if len(param) == 2:
                model_type = param[1]
            else:
                model_type = getModelType(model_file)
                if model_type == None:
                    model_type = "parallellstsmodel"
            adapter.Adapter.setParameter(self,name,model_file)
            adapter.Adapter.setParameter(self,"model_type",model_type)
        else:
            adapter.Adapter.setParameter(self,name,value)

    def getParameter(self,parametername,defaultvalue=None):
        return self._params.get(parametername,defaultvalue)

    def prepareForRun(self):
        self._is_running=True
        self.log("OK to rock")
        self._delay = int(self.getParameter("delay",0))
        if self.getParameter("model"):
            Adapter.sendInput = DelayedExecution(self,Adapter._model_guess, self._delay)
            self.log("Checking from the model")
#            from tema.model.parallellstsmodel import ParallelLstsModel as Oraakkeli
#            self._oraakkeli = Oraakkeli()
#            self._oraakkeli.loadFromFile(open(self.getParameter("model"),"r"))
            self._oraakkeli = loadModel(self.getParameter("model_type"),open(self.getParameter("model"),"r"))
            self._current_state = [self._oraakkeli.getInitialState()]
        else:
            Adapter.sendInput = DelayedExecution(self,Adapter._wild_guess, self._delay)
            self.log("Taking a guess")



    def stop(self):
        self._is_running=False

    def _breadth_first_search(self, from_state, target_actions):
        new_states=[]
        max_states=10000
        closed={}
        rval=[]
        waiting=[Transition(None,None,ss) for ss in from_state ]
        while waiting and len(closed.keys()) <= max_states :
            current_trans = waiting.pop(0)
            current_state = current_trans.getDestState()
            if  not closed.has_key(str(current_state)) :
                closed[str(current_state)] = current_trans
                for trs in current_state.getOutTransitions():
                    if self._visible :
                        self.log("Checking action: %s" % str(trs.getAction()))
                    if str(trs.getAction()) in target_actions :
                        #Found
                        rval.append(trs.getDestState())
                        closed[str(trs.getDestState())]=None
                    elif not closed.has_key(str(trs.getDestState())) \
                         and not key_word_re.match(str(trs.getAction())) :
                        waiting.append(trs)
                    else:
                        pass
        return rval


    def _model_guess(self, action_name):
        rval=True
            
        pos_states = self._breadth_first_search(self._current_state,\
                                                set([action_name]))
        neg_states = self._breadth_first_search(self._current_state,\
                                                set(["~"+action_name]))

        if pos_states and neg_states :
            if random.random() < 0.5 :
                pos_states = None
            else:
                neg_states=None

        self._last_action_name = action_name
            
        if pos_states :
            self._current_state = pos_states
            rval=True
        elif neg_states :
            self._current_state = neg_states
            rval=False
        else:
            rval=False
        pos_states=None
        neg_states=None
        self._oraakkeli.clearCache()
        self.log("Answer: %s: %s" % (action_name, str(rval)) )
        return rval

    def _wild_guess(self, action_name):
        self.log("Executing: %s" % action_name )
        rval = False
        if self._is_running :
            if self._last_action_name == action_name :
                self._last_action_cnt += 1
                if self._last_action_cnt > self._max_repetition :
                    rval= False
                else:
                    rval= True
            else:
                self._last_action_name=action_name
                self._last_action_cnt=1
                rval= True
                #if action_name=="kw_VerifyText 'Exit'":
                #    rval=False
        #self.log("We answer %s" % str(rval))
        return rval

    
    def _set_current_state_UGLY_HACK(self,state):
        self._current_state = [state]
