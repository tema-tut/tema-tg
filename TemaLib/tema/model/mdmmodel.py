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

import tema.eini.mdmparser as mdmparser
import tema.model.annotatedmodel as model

# No need to redefine Action or Transition classes

Action = model.Action

StateProp = model.StateProp

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
	def __init__(self, globalStateId, outTransitions, mdmModel=None):
		"""outTransitions is a list of Transition objects"""
		model.State.__init__(self, globalStateId, outTransitions)
		self._model = mdmModel


	def clearCache(self):
		self._outTransitions = None


	def getOutTransitions(self):
		"""Returns list of transitions that leaves the state."""
		if self._outTransitions == None:
			# If the out transitions were not already given, ask the
			# model to calculate them for us
			self._outTransitions = self._model._getOutTransitions(self._id)

		return self._outTransitions


	def getStateProps(self):
		"""Returns list of state propositions with value true on the
		state (that is, associated to the state)"""
		return self._model._getStateProps(self._id)


class MdmModel(model.Model):
	def __init__(self, mdmObject=None):
		self._stateCache = {}
		self._actionCache = {}
		self._statePropCache = {}
		self._mdm = mdmObject
		self._outgoingTransitions = {}
		if self._mdm != None:
			self._calculateTransitions()


	def clearCache(self):
		for stateId, state in self._stateCache.iteritems():
			state.clearCache()
		self._stateCache.clear()
		self._actionCache.clear()
		

	def loadFromObject(self, mdmObject):
		self.clearCache()
		self._mdm = mdmObject
		self._calculateTransitions()


	def loadFromFile(self, fileLikeObject):
		self.clearCache()
		self._mdm = mdmparser.Parser().parse(fileLikeObject)
		self._calculateTransitions()


	def _calculateTransitions(self):
		self._outgoingTransitions.clear()
		for stateId in self._mdm['states'].iterkeys():
			self._outgoingTransitions[stateId] = set()
		for transitionId, transition in self._mdm['transitions'].iteritems():
			stateId = transition['source']
			self._outgoingTransitions[stateId].add(transitionId)


	def getInitialState(self):
		return self._newState(self._mdm['properties']['initial_state']['value'])


	def getActions(self):
		return [self._newAction(k, v) for k, v in self._mdm['actions'].iteritems()]


	def getStatePropList(self):
		return [self._newStateProp(k, v) for k, v in self._mdm[mdmparser.Parser.ATTRIBUTES].iteritems()]


	def _newState(self, stateId):
		if stateId in self._stateCache:
			return self._stateCache[stateId]
		else:
			state = State(stateId, None, self)
			self._stateCache[stateId] = state
			return state


	def _newAction(self, actionId, action):
		if actionId in self._actionCache:
			return self._actionCache[actionId]
		else:
			action = Action(actionId, action['name'], action[mdmparser.Parser.AC_F_INTERESTING] != None, action[mdmparser.Parser.AC_F_COMMENT])
			self._actionCache[actionId] = action
			return action


	def _newStateProp(self, statePropId, stateProp):
		if statePropId in self._statePropCache:
			return self._statePropCache[statePropId]
		else:
			stateProp = StateProp(statePropId, stateProp['name'], stateProp[mdmparser.Parser.AT_F_INTERESTING] != None, stateProp[mdmparser.Parser.AT_F_COMMENT])
			self._statePropCache[statePropId] = stateProp
			return stateProp


	def _getOutTransitions(self, stateId):
		"""This method is called from a state object."""
		transitions = []
		for transitionId in self._outgoingTransitions[stateId]:
			transition = self._mdm['transitions'][transitionId]
			actionId = transition['action']
			transitions.append(Transition(self._newState(stateId), \
			                              self._newAction(actionId, self._mdm['actions'][actionId]), \
			                              self._newState(transition['dest'])))
		return transitions


	def _getStateProps(self, stateId):
		"""Returns the list of state propositions associated with the
		given state. This method is called from a state proposition
		object."""
		statePropIds = self._mdm[mdmparser.Parser.STATES][stateId][mdmparser.Parser.S_F_ATTRIBUTES]
		if statePropIds == None:
			statePropIds = []
		return [self._newStateProp(statePropId, self._mdm[mdmparser.Parser.ATTRIBUTES][statePropId]) for statePropId in statePropIds]


	def matchedActions(self, rexSet):
		actionNames = set()
		for actionName in [action['name'] for action in self._mdm['actions'].values()]:
			for rex in rexSet:
				if rex.match(actionName):
					actionNames.add(actionName)
					break
		return actionNames



Model=MdmModel
