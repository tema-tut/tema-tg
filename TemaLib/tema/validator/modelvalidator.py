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

import tema.model.model as model
import thread
from time import sleep

class ModelValidator:

	# Errors returned by the verification and validation functions are in form (<error_type>, <parameters>), where 
	# <parameters> is a dictionary containing the information relevant to the error.

	# error types
	NOT_STRONGLY_CONNECTED, NOT_ALWAYS_FINISHABLE, VARIED_EXECUTABILITY, ILLEGAL_ACTION_TYPE, \
        UNKNOWN_ACTION_TYPE, UNPAIRED_POSTPROCESSOR_SEPARATOR, UNPAIRED_DATA_SEPARATOR, DATA_SYNTAX_ERROR, \
        ILLEGAL_CONNECTION, TAU_USED, NONDETERMINISM, UNPAIRED_NEGATED_ACTION_WORD, RETURN_WITHOUT_END = range(13)

	# Default error messages. These messages also show what information is returned with each error.
	defaultErrorMessages = {NOT_STRONGLY_CONNECTED:           'No path to the initial state from state '\
                                                                  '%(state)s, reachable by path %(path)s.',\
	                        NOT_ALWAYS_FINISHABLE:            'No path to an end state from state %(state)s, '\
                                                                  'reachable by path %(path)s.',\
        	                VARIED_EXECUTABILITY:             'State %(state1)s, reachable by path %(path1)s, '\
                                                                  'does not allow the execution of all the actions '\
                                                                  'that state %(state2)s, reachable by path '\
                                                                  '%(path2)s, allows.',\
                	        ILLEGAL_ACTION_TYPE:              'Action %(action)s is of a type illegal in this '\
                                                                  'model.',\
                        	UNKNOWN_ACTION_TYPE:              'Action %(action)s is of an unknown type.',\
                        	UNPAIRED_POSTPROCESSOR_SEPARATOR: 'Action %(action)s has an unpaired postprocessor '\
                                                                  'separator.',\
                        	UNPAIRED_DATA_SEPARATOR:          'Action %(action)s has an unpaired data separator.',\
                        	DATA_SYNTAX_ERROR:                'Data in action %(action)s contains bad syntax.',\
                        	ILLEGAL_CONNECTION:               'Transition %(transition)s, reachable by path '\
                                                                  '%(path)s, connects two states of illegal types.',\
                        	TAU_USED:                         'Action tau used in transition %(transition)s, '\
                                                                  'reachable by path %(path)s.',\
                        	NONDETERMINISM:                   'Nondeterministic transitions detected in state '\
                                                                  '%(state)s, reachable by path %(path)s.',\
                        	UNPAIRED_NEGATED_ACTION_WORD:     'Negated transition %(transition)s, reachable by '\
                                                                  'path %(path)s, is unpaired.',\
                        	RETURN_WITHOUT_END:               'Keyword kw_return in transition %(transition)s, '\
                                                                  'reachable by path %(path)s, must be followed by a '\
                                                                  'single end_aw-synchronization.'}

	# model types, used with validation functions
	ACTION_MACHINE, REFINEMENT_MACHINE, INITIALIZATION_MACHINE, LAUNCH_MACHINE, REFINED_MACHINE,\
        COMPOSED_MACHINE = range(6)

	def __init__(self, model):
		"""Initializes a new ModelValidator object.

		The model parameter becomes the model to be initially validated. See function setModel for details."""
		self.__modelMutex = thread.allocate_lock()
		self.setModel(model)
		self.__validationMutex = thread.allocate_lock()
		self.__validations = 0
		self.__break = False

	def setModel(self, model):
		"""Sets model for validator.

		Gives the validator a new model to validate. This function must be successfully called whenever the 
		model to be validated changes in any way."""
		self.__modelMutex.acquire()
		self.__model = model
		self.__queue = [model.getInitialState()]
		self.__routes = {str(self.__queue[0]): None}
		self.__modelMutex.release()

	def beginValidation(self, modelType, errors, warnings):
		"""The complete test function.

		Performs all appropriate verifications to the given model according to its type. Each verification is 
		performed in its own thread, and this function returns once those are started. The return value is a 
		Lock object that is initially acquired; once validation is complete, the Lock is released. The 
		parameters errors and warnings are lists in which the verification functions write the errors and 
		warnings found, respectively."""
		validationLock = thread.allocate_lock()
		validationLock.acquire()
		listMutex = thread.allocate_lock()
		if modelType == ModelValidator.ACTION_MACHINE:
			self.__validationMutex.acquire()
			self.__validations = self.__validations + 1
			self.__validationMutex.release()
			threadLocks = (thread.allocate_lock(), thread.allocate_lock(), thread.allocate_lock(),\
                                       thread.allocate_lock())
			for i in threadLocks:
				i.acquire()
			thread.start_new_thread(self.verifyStronglyConnected, (errors, warnings, threadLocks[0], listMutex))
			thread.start_new_thread(self.verifyActionTypes, (errors, warnings),\
                                                {'aw': True, 'kw': False, 'ret': False, 'sync': True, 'postsync': False,\
                                                 'awsync': False, 'lock': threadLocks[1], 'listMutex': listMutex})
			thread.start_new_thread(self.verifyStateTypes, (errors, warnings),\
                                                {'isSleeping': True, 'isReady': True, 'lock': threadLocks[2],\
                                                 'listMutex': listMutex})
			thread.start_new_thread(self.verifyTransitionCombinations,\
                                                (errors, warnings, threadLocks[3], listMutex))
			thread.start_new_thread(self.__threadMonitor, (threadLocks, validationLock))
		elif modelType == ModelValidator.REFINEMENT_MACHINE:
			self.__validationMutex.acquire()
			self.__validations = self.__validations + 1
			self.__validationMutex.release()
			threadLocks = (thread.allocate_lock(), thread.allocate_lock(), thread.allocate_lock(),\
                                       thread.allocate_lock(), thread.allocate_lock())
			for i in threadLocks:
				i.acquire()
			thread.start_new_thread(self.verifyStronglyConnected, (errors, warnings, threadLocks[0], listMutex))
			thread.start_new_thread(self.verifyUnifiedExecutability,\
                                                (errors, warnings, threadLocks[1], listMutex))
			thread.start_new_thread(self.verifyActionTypes, (errors, warnings),\
                                                {'aw': False, 'kw': True, 'ret': True, 'sync': False, 'postsync': False,\
                                                 'awsync': True, 'lock': threadLocks[2], 'listMutex': listMutex})
			thread.start_new_thread(self.verifyStateTypes, (errors, warnings),\
                                                {'isSleeping': False, 'isReady': True, 'lock': threadLocks[3],\
                                                 'listMutex': listMutex})
			thread.start_new_thread(self.verifyTransitionCombinations,\
                                                (errors, warnings, threadLocks[4], listMutex))
			thread.start_new_thread(self.__threadMonitor, (threadLocks, validationLock))
		elif modelType == ModelValidator.INITIALIZATION_MACHINE:
			self.__validationMutex.acquire()
			self.__validations = self.__validations + 1
			self.__validationMutex.release()
			threadLocks = (thread.allocate_lock(), thread.allocate_lock(), thread.allocate_lock())
			for i in threadLocks:
				i.acquire()
			thread.start_new_thread(self.verifyAlwaysFinishable, (errors, warnings, threadLocks[0], listMutex))
			thread.start_new_thread(self.verifyActionTypes, (errors, warnings),\
                                                {'aw': False, 'kw': True, 'ret': False, 'sync': False, 'postsync': False,\
                                                 'awsync': False, 'lock': threadLocks[1], 'listMutex': listMutex})
			thread.start_new_thread(self.verifyTransitionCombinations,\
                                                (errors, warnings, threadLocks[2], listMutex))
			thread.start_new_thread(self.__threadMonitor, (threadLocks, validationLock))
		elif modelType == ModelValidator.LAUNCH_MACHINE:
			self.__validationMutex.acquire()
			self.__validations = self.__validations + 1
			self.__validationMutex.release()
			threadLocks = (thread.allocate_lock(), thread.allocate_lock(), thread.allocate_lock())
			for i in threadLocks:
				i.acquire()
			thread.start_new_thread(self.verifyAlwaysFinishable, (errors, warnings, threadLocks[0], listMutex))
			thread.start_new_thread(self.verifyActionTypes, (errors, warnings),\
                                                {'aw': False, 'kw': True, 'ret': False, 'sync': False, 'postsync': False,\
                                                 'awsync': False, 'lock': threadLocks[1], 'listMutex': listMutex})
			thread.start_new_thread(self.verifyTransitionCombinations,\
                                                (errors, warnings, threadLocks[2], listMutex))
			thread.start_new_thread(self.__threadMonitor, (threadLocks, validationLock))
		elif modelType == ModelValidator.REFINED_MACHINE:
			self.__validationMutex.acquire()
			self.__validations = self.__validations + 1
			self.__validationMutex.release()
			threadLocks = (thread.allocate_lock(), thread.allocate_lock(), thread.allocate_lock(),\
                                       thread.allocate_lock())
			for i in threadLocks:
				i.acquire()
			thread.start_new_thread(self.verifyStronglyConnected, (errors, warnings, threadLocks[0], listMutex))
			thread.start_new_thread(self.verifyActionTypes, (errors, warnings),\
                                                {'aw': False, 'kw': True, 'ret': False, 'sync': True, 'postsync': False,\
                                                 'awsync': True, 'lock': threadLocks[1], 'listMutex': listMutex})
			thread.start_new_thread(self.verifyStateTypes, (errors, warnings),\
                                                {'isSleeping': True, 'isReady': True, 'lock': threadLocks[2],\
                                                 'listMutex': listMutex})
			thread.start_new_thread(self.verifyTransitionCombinations,\
                                                (errors, warnings, threadLocks[3], listMutex))
			thread.start_new_thread(self.__threadMonitor, (threadLocks, validationLock))
		elif modelType == ModelValidator.COMPOSED_MACHINE:
			self.__validationMutex.acquire()
			self.__validations = self.__validations + 1
			self.__validationMutex.release()
			threadLocks = (thread.allocate_lock(), thread.allocate_lock(), thread.allocate_lock(),\
                                       thread.allocate_lock())
			for i in threadLocks:
				i.acquire()
			thread.start_new_thread(self.verifyStronglyConnected, (errors, warnings, threadLocks[0], listMutex))
			thread.start_new_thread(self.verifyActionTypes, (errors, warnings),\
                                                {'aw': False, 'kw': True, 'ret': False, 'sync': False, 'postsync': True,\
                                                 'awsync': True, 'lock': threadLocks[1], 'listMutex': listMutex})
			thread.start_new_thread(self.verifyStateTypes, (errors, warnings),\
                                                {'isSleeping': True, 'isReady': True, 'lock': threadLocks[2],\
                                                 'listMutex': listMutex})
			thread.start_new_thread(self.verifyTransitionCombinations,\
                                                (errors, warnings, threadLocks[3], listMutex))
			thread.start_new_thread(self.__threadMonitor, (threadLocks, validationLock))
		else:
			return None
		return validationLock

	def breakValidation(self):
		"""Break validations in progress.

		If called while validation is in progress, sets all verifications (and findShortestPath) to interrupt 
		in short order. This includes manually started verifications. The break order is repealed once all 
		validations finish."""
		self.__validationMutex.acquire()
		if self.__validations > 0:
			self.__break = True
		self.__validationMutex.release()

	def __threadMonitor(self, threadLocks, validationLock):
		"""Monitors the validation process.

		This function monitors all the verifications related to a validation. Once verifications are finished, 
		the lock related to the validation is released. Also, if the last validation ends, the break order is 
		repealed if set."""
		for i in threadLocks:
			i.acquire()
		self.__validationMutex.acquire()
		self.__validations = self.__validations - 1
		if self.__validations == 0:
			self.__break = False
		self.__validationMutex.release()
		validationLock.release()

	# All verification functions take as parameters two lists for error and warning messages. There are also two 
	# optional parameters for running the verification in its own thread. The lock parameter is a Lock that should 
	# be acquired before the call; once the verification is finished, the Lock is released. The listMutex parameter 
	# is also a Lock object, this one initially unlocked. It's used as a mutex when handling the list parameters.

	def verifyStronglyConnected(self, errors, warnings, lock = None, listMutex = None):
		"""Verify that the model is strongly connected.

		Meant for action machines, refinement machines, refined machines and composed machines."""
		try:
			try:
				stack = [self.__model.getInitialState()]
				transitions = {str(stack[-1]): (i for i in stack[-1].getOutTransitions())}
				dfs = {str(stack[-1]): 0}
				lowlink = {str(stack[-1]): 0}
				maxDfs = 1
				while len(stack) > 0:
					try:
						while True:
							if self.__break:
								return
							i = transitions[str(stack[-1])].next()
							if str(i.getDestState()) not in transitions:
								stack.append(i.getDestState())
								transitions[str(i.getDestState())] =\
                                                                  (i for i in stack[-1].getOutTransitions())
								dfs[str(i.getDestState())] = maxDfs
								lowlink[str(i.getDestState())] = maxDfs
								maxDfs = maxDfs + 1
							else:
								lowlink[str(stack[-1])] = min(lowlink[str(stack[-1])],\
                                                                                              lowlink[str(i.getDestState())])
					except StopIteration:
						if dfs[str(stack[-1])] == lowlink[str(stack[-1])]:
							if len(stack) != 1:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.NOT_STRONGLY_CONNECTED,\
                                                                                 {'state': stack[-1],\
                                                                                  'path': self.findShortestPath(stack[-1])}))
						if len(stack) > 1:
							lowlink[str(stack[-2])] = min(lowlink[str(stack[-2])],\
                                                                                      lowlink[str(stack[-1])])
						stack.pop()
			except SystemExit:
				pass
		finally:
			if lock != None:
				lock.release()

	def verifyAlwaysFinishable(self, errors, warnings, lock = None, listMutex = None):
		"""Verify that the model can always finish execution.

		Meant for initialization machines and launch machines."""
		try:
			try:
				stack = [self.__model.getInitialState()]
				transitions = {str(stack[-1]): (i for i in stack[-1].getOutTransitions())}
				dfs = {str(stack[-1]): 0}
				lowlink = {str(stack[-1]): 0}
				maxDfs = 1
				finishable = set([])
				while len(stack) > 0:
					try:
						while True:
							if self.__break:
								return
							i = transitions[str(stack[-1])].next()
							if str(i.getDestState()) not in transitions:
								stack.append(i.getDestState())
								transitions[str(i.getDestState())] =\
                                                                  (i for i in stack[-1].getOutTransitions())
								dfs[str(i.getDestState())] = maxDfs
								lowlink[str(i.getDestState())] = maxDfs
								maxDfs = maxDfs + 1
							else:
								lowlink[str(stack[-1])] = min(lowlink[str(stack[-1])],\
                                                                                              lowlink[str(i.getDestState())])
								if i.getDestState() in finishable or\
                                                                   lowlink[str(i.getDestState())] in finishable:
									finishable.add(stack[-1])
					except StopIteration:
						if len(stack[-1].getOutTransitions()) == 0:
							finishable.add(stack[-1])
						if dfs[str(stack[-1])] == lowlink[str(stack[-1])]:
							if stack[-1] in finishable:
								finishable.add(lowlink[str(stack[-1])])
							else:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.NOT_ALWAYS_FINISHABLE,\
                                                                                 {'state': stack[-1],\
                                                                                  'path': self.findShortestPath(stack[-1])}))
						if len(stack) > 1:
							lowlink[str(stack[-2])] = min(lowlink[str(stack[-2])],\
                                                                                      lowlink[str(stack[-1])])
							if stack[-1] in finishable or lowlink[str(stack[-1])] in finishable:
								finishable.add(stack[-2])
						stack.pop()
			except SystemExit:
				pass
		finally:
			if lock != None:
				lock.release()

	def verifyUnifiedExecutability(self, errors, warnings, lock = None, listMutex = None):
		"""Verify that any action word executable in one ready state is executable in all ready states.

		Meant for refinement machines only."""
		try:
			try:
				queue = [self.__model.getInitialState()]
				visited = set(queue)
				ready = set([])
				executables = set([i.getAction().toString() for i in queue[0].getOutTransitions()\
                                                   if i.getAction().toString()[0:2] == 'aw' or\
                                                      i.getAction().toString()[0:3] == '~aw' or\
                                                      i.getAction().toString()[0:2] == 'sv' or\
                                                      i.getAction().toString()[0:8] == 'start_aw' or\
                                                      i.getAction().toString()[0:8] == 'start_sv'])
				while len(queue) > 0:
					if self.__break:
						return
					if queue[0] in ready:
						executables2 = set([i.getAction().toString()\
                                                                    for i in queue[0].getOutTransitions()\
                                                                    if i.getAction().toString()[0:2] == 'aw' or\
                                                                       i.getAction().toString()[0:3] == '~aw' or\
                                                                       i.getAction().toString()[0:2] == 'sv' or\
                                                                       i.getAction().toString()[0:8] == 'start_aw' or\
                                                                       i.getAction().toString()[0:8] == 'start_sv'])
						for i in executables:
							if i not in executables2:
								self.__addError(warnings, listMutex,\
                                                                                (ModelValidator.VARIED_EXECUTABILITY,\
                                                                                 {'state1': queue[0],\
                                                                                  'path1': self.findShortestPath(queue[0]),\
                                                                                  'state2': self.__model.getInitialState(),\
                                                                                  'path2': []}))
								break
						for i in executables2:
							if i not in executables:
								self.__addError(warnings, listMutex,\
                                                                                (ModelValidator.VARIED_EXECUTABILITY,\
                                                                                 {'state1': self.__model.getInitialState(),\
                                                                                  'path1': [],\
                                                                                  'state2': queue[0],\
                                                                                  'path2': self.findShortestPath(queue[0])}))
								break
					for i in queue[0].getOutTransitions():
						if self.__break:
							return
						if i.getDestState() not in visited:
							queue.append(i.getDestState())
							visited.add(i.getDestState())
							if i.getAction().toString()[0:6] == 'end_aw' or\
                                                           i.getAction().toString()[0:6] == 'end_sv':
								ready.add(i.getDestState())
					queue.pop(0)
			except SystemExit:
				pass
		finally:
			if lock != None:
				lock.release()

	def verifyActionTypes(self, errors, warnings, aw, kw, ret, sync, postsync, awsync, lock = None, listMutex = None):
		"""Verify that the model only contains allowed action types.

		Meant for all machines. The parameters from aw to async determine what kinds of actions are allowed in 
		the machine: aw = action words and state verifications, kw = keywords, ret = kw_return, sync = action 
		machine synchronizations, postsync = transitions resulting in action machine synchronizations, awsync = 
		action word synchronizations. Comment transitions are always allowed. This should work as follows:
			Action machine:         aw, sync = True; kw, ret, postsync, awsync = False
			Refinement machine:     kw, ret, awsync = True; aw, sync, postsync = False
			Initialization machine: kw = True; aw, ret, sync, awsync, postsync = False
			Launch machine:         kw = True; aw, ret, sync, awsync, postsync = False
			Refined machine:        aw, kw, sync, awsync = True, ret, postsync = False
			Composed machine:       aw, kw, awsync, postsync = True, ret, sync = False"""
		try:
			try:
				for i in self.__model.getActions():
					if self.__break:
						return
					colon = i.toString().find(':')
					if i.toString()[colon+1:colon+3] == '--':
						pass
					elif i.toString()[colon+1:colon+3] == 'aw' or\
                                             i.toString()[colon+1:colon+4] == '~aw' or\
					     i.toString()[colon+1:colon+3] == 'sv':
						if not aw:
							self.__addError(errors, listMutex,\
                                                                        (ModelValidator.ILLEGAL_ACTION_TYPE, {'action': i}))
					elif i.toString()[0:2] == 'kw' or i.toString()[0:3] == '~kw' or\
                                             i.toString()[0:2] == 'vw' or i.toString()[0:3] == '~vw':
						if not kw:
							self.__addError(errors, listMutex,\
                                                                        (ModelValidator.ILLEGAL_ACTION_TYPE, {'action': i}))
						elif i.toString()[0:9] == 'kw_return':
							if not ret:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_ACTION_TYPE,\
                                                                                 {'action': i}))
						elif i.toString()[0:10] == '~kw_return':
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_ACTION_TYPE,\
                                                                                 {'action': i}))
					elif i.toString()[0:3] == 'REQ' or i.toString()[0:6] == 'REQALL' or\
                                             i.toString()[0:5] == 'ALLOW' or \
                                             i.toString() == 'WAKEts' or i.toString() == 'SLEEPts' or \
                                             i.toString()[0:7] == 'WAKEapp' or i.toString()[0:8] == 'SLEEPapp':
						if not sync:
							self.__addError(errors, listMutex,\
                                                                        (ModelValidator.ILLEGAL_ACTION_TYPE, {'action': i}))
					elif i.toString().find('ALLOWS', 0, colon+1) != -1 or\
                                             i.toString().find('WAS ALLOWED', 0, colon+1) != -1 or \
                                             i.toString()[0:13] == 'WAKEtsCANWAKE' or i.toString()[0:10] == 'WAKEtsWAKE' or\
                                             i.toString()[0:7] == 'SLEEPts' or\
                                             i.toString().find('ACTIVATES', 0, colon+1) != -1:
						if not postsync:
							self.__addError(errors, listMutex,\
                                                                        (ModelValidator.ILLEGAL_ACTION_TYPE, {'action': i}))
					elif i.toString()[colon+1:colon+9] == 'start_aw' or\
                                             i.toString()[colon+1:colon+7] == 'end_aw' or\
                                             i.toString()[colon+1:colon+8] == '~end_aw' or\
                                             i.toString()[colon+1:colon+9] == 'start_sv' or\
                                             i.toString()[colon+1:colon+7] == 'end_sv':
						if not awsync:
							self.__addError(errors, listMutex,\
                                                                        (ModelValidator.ILLEGAL_ACTION_TYPE, {'action': i}))
					elif i.toString() != 'tau':
						self.__addError(errors, listMutex,\
                                                                (ModelValidator.UNKNOWN_ACTION_TYPE, {'action': i}))
					pos = 0
					while pos < len(i.toString()):
						if self.__break:
							return
						ppBegin = i.toString().find('§', pos)
						dataBegin = i.toString().find('$(', pos)
						if ppBegin != -1 and (dataBegin == -1 or ppBegin < dataBegin):
							end = i.toString().find('§', ppBegin+1)
							if end == -1:
								self.__addError(errors, listMutex,\
                                                                     (ModelValidator.UNPAIRED_POSTPROCESSOR_SEPARATOR,\
                                                                      {'action': i}))
								break
							pos = end+1
						elif dataBegin != -1:
							end = i.toString().find(')$', dataBegin+1)
							if end == -1:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.UNPAIRED_DATA_SEPARATOR,\
                                                                                 {'action': i}))
								break
							try:
								exec(i.toString()[dataBegin+2:end])
							except SyntaxError:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.DATA_SYNTAX_ERROR,\
                                                                                 {'action': i}))
							except:
								pass
							pos = end+2
						else:
							break
			except SystemExit:
				pass
		finally:
			if lock != None:
				lock.release()

	def verifyStateTypes(self, errors, warnings, isSleeping, isReady, lock = None, listMutex = None):
		"""Verify that sleeping/awake states and ready/executing states are handled properly.

		Meant for action machines, refinement machines, refined machines and composed machines. The parameters 
		isSleeping and isReady determine the type of the initial state. This should work as follows:
			Action machine:         isSleeping = True,  isReady = True
			Refinement machine:     isSleeping = False, isReady = True
			Refined machine:        isSleeping = True,  isReady = True
			Composed machine:       isSleeping = True,  isReady = True"""
		try:
			try:
				queue = [self.__model.getInitialState()]
				visited = set(queue)
				sleeping = set([])
				awake = set([])
				ready = set([])
				executing = set([])
				if isSleeping:
					sleeping.add(self.__model.getInitialState())
				else:
					awake.add(self.__model.getInitialState())
				if isReady:
					ready.add(self.__model.getInitialState())
				else:
					executing.add(self.__model.getInitialState())
				while len(queue) > 0:
					if self.__break:
						return
					state = queue[0]
					for i in state.getOutTransitions():
						if self.__break:
							return
						colon = i.getAction().toString().find(':')
						if i.getAction().toString()[colon+1:colon+3] == '--':
							if (state in sleeping and i.getDestState() in awake) or\
                                                           (state in awake and i.getDestState() in sleeping) or\
                                                           (state in ready and i.getDestState() in executing) or\
                                                           (state in executing and i.getDestState() in ready):
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (sleeping, awake, ready, executing):
								if state in j and i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[colon+1:colon+3] == 'aw' or\
                                                     i.getAction().toString()[colon+1:colon+4] == '~aw' or\
                                                     i.getAction().toString()[colon+1:colon+3] == 'sv':
							if state in sleeping or i.getDestState() in sleeping or\
                                                           state in executing or i.getDestState() in executing:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (awake, ready):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[0:3] == 'kw_' or\
                                                     i.getAction().toString()[0:4] == '~kw_' or\
                                                     i.getAction().toString()[0:3] == 'vw_' or\
                                                     i.getAction().toString()[0:4] == '~vw_':
							if state in sleeping or i.getDestState() in sleeping or\
                                                           state in ready or i.getDestState() in ready:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (awake, executing):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[0:3] == 'REQ' or\
                                                     i.getAction().toString()[0:6] == 'REQALL' or\
                                                     i.getAction().toString()[0:10] == 'WAKEtsWAKE' or\
                                                     i.getAction().toString().find('ACTIVATES', 0, colon+1) != -1 or\
                                                     i.getAction().toString().find('ALLOWS', 0, colon+1) != -1 or\
                                                     i.getAction().toString().find('WAS ALLOWED', 0, colon+1) != -1:
							if state in sleeping or i.getDestState() in sleeping or\
                                                           state in executing or i.getDestState() in executing:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (awake, ready):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[0:5] == 'ALLOW':
							if state in awake or i.getDestState() in awake or\
                                                           state in executing or i.getDestState() in executing:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (sleeping, ready):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[0:6] == 'WAKEts' or\
                                                     i.getAction().toString()[0:7] == 'WAKEapp' or\
                                                     i.getAction().toString()[0:13] == 'WAKEtsCANWAKE':
							if state in awake or i.getDestState() in sleeping or\
                                                           state in executing or i.getDestState() in executing:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (awake, ready):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[0:7] == 'SLEEPts' or\
                                                     i.getAction().toString()[0:8] == 'SLEEPapp':
							if state in sleeping or i.getDestState() in awake or\
                                                           state in executing or i.getDestState() in executing:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (sleeping, ready):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[colon+1:colon+9] == 'start_aw' or\
                                                     i.getAction().toString()[colon+1:colon+9] == 'start_sv':
							if state in sleeping or i.getDestState() in sleeping or\
                                                           state in executing or i.getDestState() in ready:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (awake, executing):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString()[colon+1:colon+7] == 'end_aw' or\
                                                     i.getAction().toString()[colon+1:colon+8] == '~end_aw' or\
                                                     i.getAction().toString()[colon+1:colon+7] == 'end_sv':
							if state in sleeping or i.getDestState() in sleeping or\
                                                           state in ready or i.getDestState() in executing:
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.ILLEGAL_CONNECTION,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(state)}))
							for j in (awake, ready):
								if i.getDestState() not in j:
									j.add(i.getDestState())
						elif i.getAction().toString() == 'tau':
							self.__addError(errors, listMutex,\
                                                                        (ModelValidator.TAU_USED,\
                                                                         {'transition': i,\
                                                                          'path': self.findShortestPath(state)}))
						if i.getDestState() not in visited:
							queue.append(i.getDestState())
							visited.add(i.getDestState())
					queue.pop(0)
			except SystemExit:
				pass
		finally:
			if lock != None:
				lock.release()

	def verifyTransitionCombinations(self, errors, warnings, lock = None, listMutex = None):
		"""Verify that the transitions are combined correctly.

		Meant for all machines."""
		try:
			try:
				queue = [self.__model.getInitialState()]
				visited = set(queue)
				while len(queue) > 0:
					if self.__break:
						return
					if len(set([i.getAction().toString() for i in queue[0].getOutTransitions()])) <\
                                           len(queue[0].getOutTransitions()):
						self.__addError(warnings, listMutex,\
                                                                (ModelValidator.NONDETERMINISM,\
                                                                 {'state': queue[0],\
                                                                  'path': self.findShortestPath(queue[0])}))
					for i in queue[0].getOutTransitions():
						if self.__break:
							return
						if i.getAction().toString()[0:3] == '~aw':
							if i.getAction().toString()[1:] not in\
                                                           [j.getAction().toString() for j in queue[0].getOutTransitions()]:
								self.__addError(warnings, listMutex,\
                                                                       (ModelValidator.UNPAIRED_NEGATED_ACTION_WORD,\
                                                                        {'transition': i,\
                                                                         'path': self.findShortestPath(queue[0])}))
						elif i.getAction().toString()[0:9] == 'kw_return':
							if len(i.getDestState().getOutTransitions()) != 1 or\
       	                                                   i.getDestState().getOutTransitions()[0].getAction().toString()[0:4] != 'end_':
								self.__addError(errors, listMutex,\
                                                                                (ModelValidator.RETURN_WITHOUT_END,\
                                                                                 {'transition': i,\
                                                                                  'path': self.findShortestPath(queue[0])}))
						if i.getDestState() not in visited:
							queue.append(i.getDestState())
							visited.add(i.getDestState())
					queue.pop(0)
			except SystemExit:
				pass
		finally:
			if lock != None:
				lock.release()

	def findShortestPath(self, target):
		"""Find the shortest path to target state.

		Seeks the shortest path to target state, keeping the results of the search in memory to hasten future 
		searches in the same model. If the model to be searched changes in any way, the function setModel must 
		be called to reset the model information. If findShortestPath is interrupted by validation break, it 
		raises a SystemExit exception."""
		def getPath(state):
			path = []
			while self.__routes[str(state)] != None:
				path.insert(0, self.__routes[str(state)])
				state = path[0].getSourceState()
			return path
		self.__modelMutex.acquire()
		try:
			if str(target) in self.__routes:
				return getPath(target)
			while len(self.__queue) > 0:
				if self.__break:
					thread.exit()
				found = False
				for i in self.__queue[0].getOutTransitions():
					if self.__break:
						thread.exit()
					if i.getDestState() == target:
						found = True
					if str(i.getDestState()) not in self.__routes:
						self.__routes[str(i.getDestState())] = i
						self.__queue.append(i.getDestState())
				self.__queue.pop(0)
				if found:
					return getPath(target)
			return None
		finally:
			self.__modelMutex.release()

	def __addError(self, errorList, mutex, error):
		"""Adds a message to the list.

		Adds the given error message to given list, using the given Lock object as mutex."""
		if mutex != None:
			mutex.acquire()
			errorList.append(error)
			mutex.release()
		else:
			errorList.append(error)

def pruneErrors(errors):
	"""Goes through the list of errors and removes redundant ones.

	Removes from the given list those errors which are identical to another error in all respects, save 
	that a path list in error parameters may contain additional items after an identical beginning. Also 
	sorts the list."""
	sleep(0.01)
	errors.sort()
	redundant = [False for i in errors]
	for i, v in enumerate(errors):
		for j, w in enumerate(errors[i+1:]):
			if v[0] != w[0]:
				break
			difference = False
			if set(v[1].keys()) == set(w[1].keys()):
				for k in v[1].keys():
					if type(w[1][k])==list:
						if w[1][k][:len(v[1][k])] != v[1][k]:
							difference = True
							break
					else:
						if w[1][k] != v[1][k]:
							difference = True
							break
			else:
				difference = True
			if not difference:
				redundant[i+j+1] = True
	errors[:] = [v for (i, v) in enumerate(errors) if not redundant[i]]
