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

import tema.eini.einiparser as einiparser

class Parser(einiparser.Parser):
	ACTIONS			= "actions"
	ATTRIBUTES		= "stateattributes"
	STATES			= "states"
	TRANSITIONS		= "transitions"
	PROPERTIES		= "properties"

	P_I_NAME		= "name"
	P_I_INITIAL_STATE	= "initial_state"
	P_I_SNAP_TO_GRID	= "snap_to_grid"
	P_I_GRID_SIZE		= "grid_size"
	P_I_INIT_MARKER		= "init_marker"

	P_F_VALUE		= "value"
	P_F_LOCATION		= "location"
	P_F_SIZE		= "size"
	P_F_BENDPOINTS		= "bendpoints"

	AC_F_NAME		= "name"
	AC_F_INTERESTING	= "interesting"
	AC_F_COMMENT		= "comment"

	AT_F_NAME		= "name"
	AT_F_INTERESTING	= "interesting"
	AT_F_COMMENT		= "comment"

	S_F_ATTRIBUTES		= "attributes"
	S_F_LOCATION		= "location"
	S_F_SIZE		= "size"

	T_F_SOURCE		= "source"
	T_F_ACTION		= "action"
	T_F_DEST		= "dest"
	T_F_BENDPOINTS		= "bendpoints"

	__ERROR_N_ENTITY	= "Entity '%s' must be defined."
	__ERROR_N_INSTANCE	= "Instance '%s' must be defined for the entity '%s'."
	__ERROR_A		= "Field '%s' must be defined for the entity '%s'."
	__ERROR_A_INSTANCE	= "Field '%s' must be defined for the instance '%s' of the entity '%s'."
	__ERROR_T_STR		= "Field '%s' of the entity '%s' may not be a list."
	__ERROR_T_LIST		= "Field '%s' of the entity '%s' must be a list."
	__ERROR_V_EMPTY		= "Value of the field '%s' of the instance '%s' of the entity '%s' may not be empty."
	__ERROR_V_REF		= "Value of the field '%s' of the instance '%s' of the entity '%s' must refer to an " \
                                  "instance of the entity '%s'."
	__ERROR_V_REFS		= "Value of the field '%s' of the instance '%s' of the entity '%s' must refer to " \
                                  "instances of the entity '%s'."
	__ERROR_V_DUPLICATE	= "Values of the field '%s' of the instances of the entity '%s' must be unique."
	__ERROR_V_ID		= "Identifier '%s' of the entity '%s' must be an integer."
	__ERROR_V_INT		= "Value of the field '%s' of the instance '%s' of the entity '%s' must be an integer."
	__ERROR_V_INT_LIST	= "Value of the field '%s' of the instance '%s' of the entity '%s' must be a list of " \
                                  "integers."
	__ERROR_V_INT_PAIR	= "Value of the field '%s' of the instance '%s' of the entity '%s' must be a pair of " \
                                  "integers."
	__ERROR_V_INT_LIST_LIST = "Value of the field '%s' of the instance '%s' of the entity '%s' must be a list of " \
                                  "lists of integers."



	def parse(self, fileobj):
		result=einiparser.Parser.parse(self, fileobj)

 		if Parser.ACTIONS not in result:
			actions = einiparser.Entity()
			actions.fields()[Parser.AC_F_NAME] = str
			result[Parser.ACTIONS] = actions
		self.__handleActions(result[Parser.ACTIONS])

		if Parser.ATTRIBUTES not in result:
			attributes = einiparser.Entity()
			attributes.fields()[Parser.AT_F_NAME] = str
			result[Parser.ATTRIBUTES] = attributes
		self.__handleAttributes(result[Parser.ATTRIBUTES])

		if Parser.STATES not in result:
			raise NameError(Parser.__ERROR_N_ENTITY % Parser.STATES)
		self.__handleStates(result[Parser.STATES], result[Parser.ATTRIBUTES])

		if Parser.TRANSITIONS not in result:
			transitions = einiparser.Entity()
			transitions.fields()[Parser.T_F_SOURCE] = str
			transitions.fields()[Parser.T_F_ACTION] = str
			transitions.fields()[Parser.T_F_DEST] = str
			result[Parser.TRANSITIONS] = transitions
		self.__handleTransitions(result[Parser.TRANSITIONS], result[Parser.ACTIONS], result[Parser.STATES])

		if Parser.PROPERTIES not in result:
			raise NameError(Parser.__ERROR_N_ENTITY % Parser.PROPERTIES)
		self.__handleProperties(result[Parser.PROPERTIES], result[Parser.STATES])

		return result



	def __handleActions(self, actions):
		if Parser.AC_F_NAME not in actions.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.AC_F_NAME, Parser.ACTIONS))
		if Parser.AC_F_INTERESTING not in actions.fields():
			actions.fields()[Parser.AC_F_INTERESTING] = str
			for v in actions.itervalues():
				v[Parser.AC_F_INTERESTING] = None
		if Parser.AC_F_COMMENT not in actions.fields():
			actions.fields()[Parser.AC_F_COMMENT] = str
			for v in actions.itervalues():
				v[Parser.AC_F_COMMENT] = None

		if actions.fields()[Parser.AC_F_NAME] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.AC_F_NAME, Parser.ACTIONS))
		if actions.fields()[Parser.AC_F_INTERESTING] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.AC_F_INTERESTING, Parser.ACTIONS))
		if actions.fields()[Parser.AC_F_COMMENT] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.AC_F_COMMENT, Parser.ACTIONS))

		self.__convertKeys(actions, Parser.ACTIONS)

		names = {}
		for k, v in actions.iteritems():
			if len(v[Parser.AC_F_NAME]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % (Parser.AC_F_NAME, k, Parser.ACTIONS))
			if v[Parser.AC_F_NAME] in names:
				raise ValueError(Parser.__ERROR_V_DUPLICATE % (Parser.AC_F_NAME, Parser.ACTIONS))
			names[v[Parser.AC_F_NAME]] = None



	def __handleAttributes(self, attributes):
		if Parser.AT_F_NAME not in attributes.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.AT_F_NAME, Parser.ATTRIBUTES))
		if Parser.AT_F_INTERESTING not in attributes.fields():
			attributes.fields()[Parser.AT_F_INTERESTING] = str
			for v in attributes.itervalues():
				v[Parser.AT_F_INTERESTING] = None
		if Parser.AT_F_COMMENT not in attributes.fields():
			attributes.fields()[Parser.AT_F_COMMENT] = str
			for v in attributes.itervalues():
				v[Parser.AT_F_COMMENT] = None

		if attributes.fields()[Parser.AT_F_NAME] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.AT_F_NAME, Parser.ATTRIBUTES))
		if attributes.fields()[Parser.AT_F_INTERESTING] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.AT_F_INTERESTING, Parser.ATTRIBUTES))
		if attributes.fields()[Parser.AT_F_COMMENT] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.AT_F_COMMENT, Parser.ATTRIBUTES))

		self.__convertKeys(attributes, Parser.ATTRIBUTES)

		names = {}
		for k, v in attributes.iteritems():
			if len(v[Parser.AT_F_NAME]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % (Parser.AT_F_NAME, k, Parser.ATTRIBUTES))
			if v[Parser.AT_F_NAME] in names:
				raise ValueError(Parser.__ERROR_V_DUPLICATE % (Parser.AT_F_NAME, Parser.ATTRIBUTES))
			names[v[Parser.AT_F_NAME]] = None



	def __handleStates(self, states, attributes):
		if Parser.S_F_ATTRIBUTES not in states.fields():
			states.fields()[Parser.S_F_ATTRIBUTES] = list
			for v in states.itervalues():
				v[Parser.S_F_ATTRIBUTES] = None
		if Parser.S_F_LOCATION not in states.fields():
			states.fields()[Parser.S_F_LOCATION] = list
			for v in states.itervalues():
				v[Parser.S_F_LOCATION] = None
		if Parser.S_F_SIZE not in states.fields():
			states.fields()[Parser.S_F_SIZE] = list
			for v in states.itervalues():
				v[Parser.S_F_SIZE] = None

		if states.fields()[Parser.S_F_ATTRIBUTES] != list:
			raise TypeError(Parser.__ERROR_T_LIST % (Parser.S_F_ATTRIBUTES, Parser.STATES))
		if states.fields()[Parser.S_F_LOCATION] != list:
			raise TypeError(Parser.__ERROR_T_LIST % (Parser.S_F_LOCATION, Parser.STATES))
		if states.fields()[Parser.S_F_SIZE] != list:
			raise TypeError(Parser.__ERROR_T_LIST % (Parser.S_F_SIZE, Parser.STATES))

		self.__convertKeys(states, Parser.STATES)

		for k, v in states.iteritems():
			if v[Parser.S_F_ATTRIBUTES] != None:
				for i, w in enumerate(v[Parser.S_F_ATTRIBUTES]):
					try:
						v[Parser.S_F_ATTRIBUTES][i] = self.__parseInt(w)
					except ValueError:
						raise ValueError(Parser.__ERROR_V_INT_LIST % \
                                                                 (Parser.S_F_ATTRIBUTES, k, Parser.STATES))
					if v[Parser.S_F_ATTRIBUTES][i] not in attributes:
						raise ValueError(Parser.__ERROR_V_REFS % \
                                                                 (Parser.S_F_ATTRIBUTES, k, Parser.STATES, \
                                                                  Parser.ATTRIBUTES))

			if v[Parser.S_F_LOCATION] != None:
				try:
					v[Parser.S_F_LOCATION] = self.__parseXY(v[Parser.S_F_LOCATION])
				except ValueError:
					raise ValueError(Parser.__ERROR_V_INT_PAIR % \
                                                         (Parser.S_F_LOCATION, k, Parser.STATES))

			if v[Parser.S_F_SIZE] != None:
				try:
					v[Parser.S_F_SIZE] = self.__parseXY(v[Parser.S_F_SIZE])
				except ValueError:
					raise ValueError(Parser.__ERROR_V_INT_PAIR % (Parser.S_F_SIZE, k, Parser.STATES))



	def __handleTransitions(self, transitions, actions, states):
		if Parser.T_F_SOURCE not in transitions.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.T_F_SOURCE, Parser.TRANSITIONS))
		if Parser.T_F_ACTION not in transitions.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.T_F_ACTION, Parser.TRANSITIONS))
		if Parser.T_F_DEST not in transitions.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.T_F_DEST, Parser.TRANSITIONS))
		if Parser.T_F_BENDPOINTS not in transitions.fields():
			transitions.fields()[Parser.T_F_BENDPOINTS] = list
			for v in transitions.itervalues():
				v[Parser.T_F_BENDPOINTS] = None

		if transitions.fields()[Parser.T_F_SOURCE] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.T_F_SOURCE, Parser.TRANSITIONS))
		if transitions.fields()[Parser.T_F_ACTION] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.T_F_ACTION, Parser.TRANSITIONS))
		if transitions.fields()[Parser.T_F_DEST] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.T_F_DEST, Parser.TRANSITIONS))
		if transitions.fields()[Parser.T_F_BENDPOINTS] != list:
			raise TypeError(Parser.__ERROR_T_LIST % (Parser.T_F_BENDPOINTS, Parser.TRANSITIONS))

		self.__convertKeys(transitions, Parser.TRANSITIONS)

		for k, v in transitions.iteritems():
			try:
				v[Parser.T_F_SOURCE] = self.__parseInt(v[Parser.T_F_SOURCE])
			except ValueError:
				raise ValueError(Parser.__ERROR_V_INT % (Parser.T_F_SOURCE, k, Parser.TRANSITIONS))
			if v[Parser.T_F_SOURCE] not in states:
				raise ValueError(Parser.__ERROR_V_REF % \
                                                 (Parser.T_F_SOURCE, k, Parser.TRANSITIONS, Parser.STATES))

			try:
				v[Parser.T_F_ACTION] = self.__parseInt(v[Parser.T_F_ACTION])
			except ValueError:
				raise ValueError(Parser.__ERROR_V_INT % (Parser.T_F_ACTION, k, Parser.TRANSITIONS))
			if v[Parser.T_F_ACTION] not in actions:
				raise ValueError(Parser.__ERROR_V_REF % \
                                                 (Parser.T_F_ACTION, k, Parser.TRANSITIONS, Parser.ACTIONS))

			try:
				v[Parser.T_F_DEST] = self.__parseInt(v[Parser.T_F_DEST])
			except ValueError:
				raise ValueError(Parser.__ERROR_V_INT % (Parser.T_F_DEST, k, Parser.TRANSITIONS))
			if v[Parser.T_F_DEST] not in states:
				raise ValueError(Parser.__ERROR_V_REF % \
                                                 (Parser.T_F_DEST, k, Parser.TRANSITIONS, Parser.STATES))

			if v[Parser.T_F_BENDPOINTS] != None:
				try:
					v[Parser.T_F_BENDPOINTS] = self.__parseBendpoints(v[Parser.T_F_BENDPOINTS])
				except ValueError:
					raise ValueError(Parser.__ERROR_V_INT_LIST_LIST % \
                                                         (Parser.T_F_BENDPOINTS, k, Parser.TRANSITIONS))

		transitions.fields()[Parser.T_F_SOURCE] = int
		transitions.fields()[Parser.T_F_ACTION] = int
		transitions.fields()[Parser.T_F_DEST] = int



	def __handleProperties(self, properties, states):
                if Parser.P_F_VALUE not in properties.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.P_F_VALUE, Parser.PROPERTIES))
		if Parser.P_F_LOCATION not in properties.fields():
			properties.fields()[Parser.P_F_LOCATION] = list
			for v in properties.itervalues():
				v[Parser.P_F_LOCATION] = None
		if Parser.P_F_SIZE not in properties.fields():
			properties.fields()[Parser.P_F_SIZE] = list
			for v in properties.itervalues():
				v[Parser.P_F_SIZE] = None
		if Parser.P_F_BENDPOINTS not in properties.fields():
			properties.fields()[Parser.P_F_BENDPOINTS] = list
			for v in properties.itervalues():
				v[Parser.P_F_BENDPOINTS] = None

		if properties.fields()[Parser.P_F_VALUE] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.P_F_VALUE, Parser.PROPERTIES))
		if properties.fields()[Parser.P_F_LOCATION] != list:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.P_F_LOCATION, Parser.PROPERTIES))
		if properties.fields()[Parser.P_F_SIZE] != list:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.P_F_SIZE, Parser.PROPERTIES))
		if properties.fields()[Parser.P_F_BENDPOINTS] != list:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.P_F_BENDPOINTS, Parser.PROPERTIES))

		if Parser.P_I_NAME not in properties:
			raise NameError(Parser.__ERROR_N_INSTANCE % (Parser.P_I_NAME, Parser.PROPERTIES))
		if Parser.P_I_INITIAL_STATE not in properties:
			raise NameError(Parser.__ERROR_N_INSTANCE % (Parser.P_I_INITIAL_STATE, Parser.PROPERTIES))
		if Parser.P_I_SNAP_TO_GRID not in properties:
			properties[Parser.P_I_SNAP_TO_GRID] = {Parser.P_F_VALUE: None}
		if Parser.P_I_GRID_SIZE not in properties:
			properties[Parser.P_I_GRID_SIZE] = {Parser.P_F_VALUE: None}
		if Parser.P_I_INIT_MARKER not in properties:
			properties[Parser.P_I_INIT_MARKER] = {Parser.P_F_LOCATION: None, Parser.P_F_SIZE: None, \
                                                                Parser.P_F_BENDPOINTS: None}

		if len(properties[Parser.P_I_NAME][Parser.P_F_VALUE]) == 0:
			raise ValueError(Parser.__ERROR_V_EMPTY % \
                                         (Parser.P_F_VALUE, Parser.P_I_NAME, Parser.PROPERTIES))

		try:
			properties[Parser.P_I_INITIAL_STATE][Parser.P_F_VALUE] = \
                                self.__parseInt(properties[Parser.P_I_INITIAL_STATE][Parser.P_F_VALUE])
		except ValueError:
			raise ValueError(Parser.__ERROR_V_INT % \
                                         (Parser.P_F_VALUE, Parser.P_I_INITIAL_STATE, Parser.PROPERTIES))
		if properties[Parser.P_I_INITIAL_STATE][Parser.P_F_VALUE] not in states:
			raise ValueError(Parser.__ERROR_V_REF % \
                                         (Parser.P_F_VALUE, Parser.P_I_INITIAL_STATE, Parser.PROPERTIES, \
                                          Parser.STATES))

		if properties[Parser.P_I_INIT_MARKER][Parser.P_F_LOCATION] != None:
			try:
				properties[Parser.P_I_INIT_MARKER][Parser.P_F_LOCATION] = \
                                        self.__parseXY(properties[Parser.P_I_INIT_MARKER][Parser.P_F_LOCATION])
			except ValueError:
				raise ValueError(Parser.__ERROR_V_INT_PAIR % \
                                                 (Parser.P_F_LOCATION, Parser.P_I_INIT_MARKER, Parser.PROPERTIES))

		if properties[Parser.P_I_INIT_MARKER][Parser.P_F_SIZE] != None:
			try:
				properties[Parser.P_I_INIT_MARKER][Parser.P_F_SIZE] = \
                                        self.__parseXY(properties[Parser.P_I_INIT_MARKER][Parser.P_F_SIZE])
			except ValueError:
				raise ValueError(Parser.__ERROR_V_INT_PAIR % \
                                                 (Parser.P_F_SIZE, Parser.P_I_INIT_MARKER, Parser.PROPERTIES))

		if properties[Parser.P_I_INIT_MARKER][Parser.P_F_BENDPOINTS] != None:
			try:
				properties[Parser.P_I_INIT_MARKER][Parser.P_F_BENDPOINTS] = \
                                        self.__parseBendpoints(properties[Parser.P_I_INIT_MARKER][Parser.P_F_BENDPOINTS])
			except ValueError:
				raise ValueError(Parser.__ERROR_V_INT_LIST_LIST % \
                                                 (Parser.P_F_BENDPOINTS, Parser.P_I_INIT_MARKER, Parser.PROPERTIES))



	def __convertKeys(self, entity, entityName):
		newItems = []

		for k, v in entity.iteritems():
			try:
				newItems.append((self.__parseInt(k), v))
			except ValueError:
				raise ValueError(Parser.__ERROR_V_ID % (k, entityName))

		entity.clear()

		for i in newItems:
			entity[i[0]] = i[1]



	def __parseBendpoints(self, list):
		bendpoints = []

		for i, v in enumerate(list):
			point = v.split(':')
			if len(point) != 2:
				raise ValueError()
			bendpoints.append([self.__parseInt(point[0]), self.__parseInt(point[1])])

		return bendpoints



	def __parseXY(self, list):
		if len(list) != 2:
			raise ValueError()
		return [self.__parseInt(list[0]), self.__parseInt(list[1])]



	def __parseInt(self, string):
		try:
			return int(string)
		except:
			raise ValueError()
