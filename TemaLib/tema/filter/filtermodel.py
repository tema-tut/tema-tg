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

# No need to redefine Action or Transition classes

Action = model.Action

Transition = model.Transition



class State(model.State):
	"""
	State class is redefined to support on-the-fly generation of the
	state space: not all State and Transition objects need to be
	generated at once. If outTransitions list is None and
	getOutTransitions method is called, the mdm model is asked to
	generate outTransitions for the state. The result is stored so
	next time the generation is not needed.
	"""
	def __init__(self, state, filterModel):
		model.State.__init__(self, state._id, None)
		self._state = state
		self._model = filterModel


	def getOutTransitions(self):
		"""Returns list of transitions that leaves the state."""
		if self._outTransitions == None:
			# If the out transitions were not already given, ask the
			# model to calculate them for us
			self._outTransitions = self._model._getOutTransitions(self._state)
		
		return self._outTransitions



class FilterModel(model.Model):
	def __init__(self, modelObject=None, forbiddenActions=None):
		self._stateCache = {}
		self._model = modelObject
		if forbiddenActions != None:
			self._forbidden = frozenset(forbiddenActions)
		else:
			self._forbidden = None


	def clearCache(self):
		if self._model != None:
			self._model.clearCache()
		self._stateCache.clear()
		

	def loadFromObject(self, modelObject):
		self.clearCache()
		self._model = modelObject


	def setForbiddenActions(self, forbiddenActions):
		self._forbidden = frozenset(forbiddenActions)


	def getForbiddenActions(self):
		return self._forbidden


	def getInitialState(self):
		return self._newState(self._model.getInitialState())


	def getActions(self):
		return self._model.getActions()


	def _newState(self, state):
		if state in self._stateCache:
			return self._stateCache[state]
		else:
			newState = State(state, self)
			self._stateCache[state] = newState
			return newState


	def _getOutTransitions(self, state):
		return [Transition(self._newState(transition.getSourceState()), transition.getAction(), self._newState(transition.getDestState())) \
                        for transition in state.getOutTransitions() \
                        if str(transition.getAction()) not in self._forbidden]



Model=FilterModel
