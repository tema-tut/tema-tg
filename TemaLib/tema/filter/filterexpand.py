#!/usr/bin/env python
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

import re
import sys
import os

from tema.model.lstsmodel import Model
from tema.rules.rules_parser import ExtRulesParser



usage = """
Usage: filterexpand [print_option] rulesfile forbidden1 forbidden2... -m model1 forbidden1-1 forbidden1-2... -m model2 forbidden2-1 forbidden 2-2... model3...

print_option = -all | -process | -minimalactions | -actions | -rules

Examples:
filterexpand combined-rules.ext
filterexpand -minimalactions combined-rules.ext -m Messaging-Startup start_awStartMessaging
filterexpand combined-rules.ext "kw_VerifyText.*"
"""

BAN_NORULE = 'nr'
BAN_MISSINGACTION = 'ma'
BAN_STRONGCONNECTIVITY = 'sc'
BAN_UNREACHABLE = 'ur'

PRINT_ALL = ~0
PRINT_PROCESS = 1 << 0
PRINT_MINIMALACTIONS = 1 << 1
PRINT_NONMINIMALACTIONS = 1 << 2
PRINT_ACTIONS = PRINT_MINIMALACTIONS | PRINT_NONMINIMALACTIONS
PRINT_RULES = 1 << 3
PRINT_RULESFILE = 1 << 4 

class ModelInfo:
	def __init__(self, name, model):
		self.__name = name
		self.__model = model
		self.__name2action = dict([(str(a), a) for a in self.__model.getActions()])
		self.__actions = set([str(action) for action in self.__model.getActions()])

		self.__forbidden = set()

		self.__isc = None
		self.__haschanged = True

	def __str__(self):
		return self.__name

	def actions(self):
		return self.__actions

	def negate(self, actionname):
		negation = self.__name2action[actionname].negate()
		if negation in self.__name2action:
			return negation
		else:
			return None

	def opposites(self, actionname):
		opposites = []
		if actionname.startswith('start_aw'):
			opposites.append('end_aw' + actionname[len('start_aw'):])
			opposites.append('~end_aw' + actionname[len('start_aw'):])
		elif actionname.startswith('end_aw'):
			opposites.append('start_aw' + actionname[len('end_aw'):])
		elif actionname.startswith('~end_aw'):
			opposites.append('start_aw' + actionname[len('~end_aw'):])

		return [a for a in opposites if a in self.__name2action]

	def forbid(self, actionname):
		if actionname in self.__name2action and actionname not in self.__forbidden:
			self.__forbidden.add(actionname)

			negation = self.__name2action[actionname].negate()

			if negation in self.__name2action:
				self.__forbidden.add(negation)

			self.__isc = None
			self.__haschanged = True

	def forbidden(self, actionname):
		return actionname in self.__forbidden

	def haschanged(self):
		return self.__haschanged

	def isc(self):
		def tarjan(state, index):
			indices[state] = index
			lowlinks[state] = index
			index = index + 1
			stack.append(state)
			for transition in state.getOutTransitions():
				if str(transition.getAction()) not in self.__forbidden:
					dest = transition.getDestState()
					if dest not in indices:
						tarjan(dest, index)
						lowlinks[state] = min(lowlinks[state], lowlinks[dest])
					elif dest in stack:
						lowlinks[state] = min(lowlinks[state], lowlinks[dest])
#						lowlinks[state] = min(lowlinks[state], indices[dest])
			if indices[state] == 0:
				return set(stack)
			elif lowlinks[state] == indices[state]:
				state2 = stack.pop()
				while state2 != state:
					state2 = stack.pop()

		if self.__haschanged:
			stack = []
			indices = {}
			lowlinks = {}
			self.__isc = tarjan(self.__model.getInitialState(), 0)
			self.__haschanged = False

		return self.__isc



class Rule:
	def __init__(self, extrule):
		self.__modelactions = extrule[:-1]
		self.__syncaction = extrule[-1]

	def modelactions(self):
		return self.__modelactions

	def syncaction(self):
		return self.__syncaction

	def extrule(self):
		return self.__modelactions + [self.__syncaction]

	def __hash__(self):
		h = hash(self.__syncaction)
		for modelaction in self.__modelactions:
			h += hash(modelaction)
		return h

	def __str__(self):
		s = ''
		for modelaction in self.__modelactions:
			s += ' (' + modelaction[0] + ',"' + modelaction[1] + '")'
		s += ' -> "' + self.__syncaction + '"'
		return s.strip()



class InputError(StandardError):
	pass



def expand(parallelfile_content, path, forbidden_acts, forbidden_sync_patterns):
	def addunhandledaction(model, action):
		unhandled_actions.add((model, action))
		changed_models.add(model)

		modelinfo = models[model]
		negation = modelinfo.negate(action)
		if negation != None:
			unhandled_actions.add((model, negation))

		for a in modelinfo.opposites(action):
			unhandled_actions.add((model, a))

	models = {}

	parser = ExtRulesParser()
	files = parser.parseLstsFiles(parallelfile_content)
	for name, filename in files:
		model = Model()
		f = open(path + filename)
		try:
			model.loadFromFile(f)
		finally:
			f.close()
		models[name] = ModelInfo(name, model)

	forbidden_actions = set()
	unhandled_actions = set()
	forbidden_rules = set()
	unhandled_rules = set()
	unforbidden_rules = {}
	changed_models = set()

	process = []

	for name, model in models.iteritems():
		changed_models.add(name)
		for action in forbidden_acts.get(name, []):
			if action in model.actions():
				addunhandledaction(name, action)
		for action in model.actions():
			unforbidden_rules[(name, action)] = set()

	extrules = parser.parseRules(parallelfile_content)
	for extrule in extrules:
		rule = Rule(extrule)
		for pattern in forbidden_sync_patterns:
			if pattern.match(rule.syncaction()):
				unhandled_rules.add(rule)
				break
		for modelaction in rule.modelactions():
			if modelaction in unforbidden_rules:
				unforbidden_rules[modelaction].add(rule)

	for (model, action), rules in unforbidden_rules.iteritems():
		if len(rules) == 0:
			addunhandledaction(model, action)
#			print 'pc:', (model, action)
			process.append((BAN_NORULE, (model, action)))

	while len(unhandled_actions) > 0 or len(unhandled_rules) > 0:
		while len(unhandled_actions) > 0 or len(unhandled_rules) > 0:
			for modelaction in unhandled_actions:
				for rule in unforbidden_rules[modelaction]:
					if rule not in forbidden_rules:
						unhandled_rules.add(rule)
#						print 'ma:', rule
						process.append((BAN_MISSINGACTION, rule))
				unforbidden_rules[modelaction].clear()
			forbidden_actions.update(unhandled_actions)
			for model, action in unhandled_actions:
				models[model].forbid(action)
			unhandled_actions.clear()

			for rule in unhandled_rules:
				for modelaction in rule.modelactions():
					unforbidden_rules[modelaction].discard(rule)
					if len(unforbidden_rules[modelaction]) == 0 and modelaction not in forbidden_actions:
						addunhandledaction(modelaction[0], modelaction[1])
#						print 'pc:', modelaction
						process.append((BAN_NORULE, modelaction))
			forbidden_rules.update(unhandled_rules)
			unhandled_rules.clear()

		while len(changed_models) > 0 and len(unhandled_actions) == 0:
			name = changed_models.pop()
			model = models[name]
			reachables = set()
			for state in model.isc():
				for transition in state.getOutTransitions():
					action = str(transition.getAction())
					reachables.add(action)
					if transition.getDestState() not in model.isc() and (name, action) not in forbidden_actions:
						addunhandledaction(name, action)
#						print 'sc:', (name, action)
						process.append((BAN_STRONGCONNECTIVITY, (name, action)))
			for action in model.actions():
				if action not in reachables and (name, action) not in forbidden_actions:
					addunhandledaction(name, action)
#					print 'ur:', (name, action)
					process.append((BAN_UNREACHABLE, (name, action)))

	return (process, models)

	minimal_forbidden_actions = set()
	for name, model in models.iteritems():
		for state in model.isc():
			for transition in state.getOutTransitions():
				action = str(transition.getAction())
				if model.forbidden(action):
					minimal_forbidden_actions.add((name, action))

	return process, minimal_forbidden_actions, (forbidden_actions - minimal_forbidden_actions), forbidden_rules



def getprocess(results):
	return results[0]



def getactions(results):
	actions = {}
	for item in results[0]:
		if item[0] != BAN_MISSINGACTION:
			model, action = item[1]
			if model not in actions:
				actions[model] = set()
			actions[model].add(action)

	return actions



def getminimalactions(results):
	minimalactions = {}
	for name, model in results[1].iteritems():
		for state in model.isc():
			for transition in state.getOutTransitions():
				action = str(transition.getAction())
				if model.forbidden(action):
					if name not in minimalactions:
						minimalactions[name] = set()
					minimalactions[name].add(action)

	return minimalactions



def getnonminimalactions(results, actions = None, minimalactions = None):
	if actions == None:
		actions = getactions(results)
	if minimalactions == None:
		minimalactions = getminimalactions(results)

	nonminimalactions = {}
	for model, actions in actions:
		if model in minimalactions:
			actionsdiff = actions - minimalactions[model]
		else:
			actionsdiff = set()

		if len(actionsdiff > 0):
			nonminimalactions[model] = actionsdiff

	return nonminimalactions



def getrules(results):
	rules = set()
	for item in results[0]:
		if item[0] == BAN_MISSINGACTION:
			rules.add(item[1])
	return rules

def printrulesfile(results,oldrules):
	
	file = open(oldrules,"r")
	newrules = ""
	forbiddenrules = set([str(rule) for rule in getrules(results)])
	
	line = file.readline()
	while len(line) > 0 and line[0] != "(":
		newrules += line
		line = file.readline()
	
	while len(line) > 0:
	
		if line.strip() not in forbiddenrules:
			newrules += line
		line = file.readline()
	
	print newrules
	
	

def printresults(mode, results):
	def match(flag):
		return (flag & mode) == flag

	def printactions(actionsdict):
		modelactions = [(model, [action for action in actions]) for model, actions in actionsdict.iteritems()]
		modelactions.sort()
		for model, actions in modelactions:
			actions.sort()

		for model, actions in modelactions:
			print model + ':',
			for action in actions:
				print '"' + action + '"',
			print

	if match(PRINT_PROCESS):
		for id, ban in getprocess(results):
			print id + ': ' + str(ban)

	if match(PRINT_ACTIONS):
		printactions(getactions(results))
	elif match(PRINT_MINIMALACTIONS):
		printactions(getminimalactions(results))
	elif match(PRINT_NONMINIMALACTIONS):
		printactions(getnonminimalactions(results))

	if match(PRINT_RULES):
		rules = [rule for rule in getrules(results)]
		rules.sort()
		for rule in rules:
			print rule



def main():
	STATE_INIT = 0
	STATE_MODEL = 1
	STATE_ACTION = 2

	try:
		forbidden_actions = {}
		print_mode = PRINT_ALL

		state = STATE_INIT
		for arg in sys.argv[1:]:
			if state == STATE_INIT:
				if arg[0] == '-':
					try:
						print_mode = eval('PRINT_' + arg[1:].upper())
					except NameError:
						raise InputError(usage)

				else:
					rulesfile = arg
					forbidden_latest = set()
					forbidden_syncs = forbidden_latest
					state = STATE_ACTION

			elif state == STATE_MODEL:
				forbidden_latest = set()
				forbidden_actions[arg] = forbidden_latest
				state = STATE_ACTION

			elif state == STATE_ACTION:
				if arg == '-m':
					state = STATE_MODEL
				else:
					forbidden_latest.add(arg)
		if state != STATE_ACTION:
			raise InputError(usage)

		f = open(rulesfile)
		try:
			content = f.read()
		finally:
			f.close()

		results = expand(content, rulesfile[0:rulesfile.rfind(os.sep) + 1], forbidden_actions, [re.compile(s) for s in forbidden_syncs])
		
		if (PRINT_RULESFILE & print_mode) == PRINT_RULESFILE:
			printrulesfile(results,rulesfile)
		else:
			printresults(print_mode, results)

	except InputError, e:
		print e



if __name__ == '__main__':
	main()
