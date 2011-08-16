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

import tema.model.model as model


Action = model.Action

Transition = model.Transition


class State(model.State):
    """
    State class contains the id of a state the transitions that leave
    the state.
    """
    def __init__(self,globalStateId):
        self._id=globalStateId
        
    def __str__(self):
        return str(self._id)

    def getOutTransitions(self):
        """Returns list of transitions that leaves the state."""
	if self._id == 0:
		return [Transition(self, forward, getState(self._id+1))]
	else:
		return [Transition(self, backward, getState(self._id-1)), Transition(self, forward, getState(self._id+1))]
    
    def execAction(self,action):
        """Returns the destination state of the first transition that
        leaves this state and is labelled by the action. If there is
        no such transition, returns None."""
	if action == forward:
		return getState(self._id+1)
	elif action == backward and self._id > 0:
		return getState(self._id-1)
	else:
		return None

    def equals(self,state):
        return self._id==state._id


class InfiniteModel(model.Model):
    def __init__(self):
        pass

    def loadFromObject(self,input_object):
	pass

    def loadFromFile(self,file_like_object):
	pass

    def getInitialState(self):
	return getState(0)

    def getActions(self):
	return [forward, backward]


Model = InfiniteModel

forward = Action(0, 'kw_Forward')
backward = Action(1, 'kw_Backward')

states = []

def getState(id):
	while len(states) <= id:
		states.append(State(len(states)))
	return states[id]
