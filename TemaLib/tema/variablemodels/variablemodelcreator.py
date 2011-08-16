#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import tema.lsts.lsts as lsts
import optparse


"""
Generates variable models and interface model from a list of variables

Variable file format:

Variable1Name: value1,value2,value3
Variable2Name: (UnknownValue),value1,value2 


The first value in the list is the initial value. Value enclosed with parantheses is the unknown value

"""

class Variable:

	def __init__(self,name,values, unknownValue):
		self.__name = name
		self.__values = values
		self.__unknownValue = unknownValue
		
	def getName(self):
		return self.__name
	
	def getValues(self):
		return self.__values
		
	def getUnknownValue(self):
		return self.__unknownValue
		
	def getActions(self):
		
		VerifyAllowActions = []
		toAllowActions = []

		for v in self.__values:
		
			VerifyAllowActions.append("ALLOW<@PARENT: " + self.__name + v + ">")
			toAllowActions.append("ALLOW<@PARENT: To" + self.__name + v + ">")		
		
		return VerifyAllowActions, toAllowActions
		
		
class VariableModelCreator:


	def __init__(self,file,output):
		self.__variable_file = file	
		self.__variables = []
		self.__outputDir = output
		
		
	def readVariables(self):

		if(not os.path.exists(self.__variable_file)):
			print "File:" + self.__variable_file + " does not exist"
			
		try:
			file = open(self.__variable_file, "r")
			
			for variable in open(self.__variable_file,"r").readlines():
				variable = file.readline()
				variableName = variable.partition(":")[0]
				unknownValue = None
				
				variableValues = [v.strip() for v in variable.partition(":")[2].split(",")]
				
				for v in variableValues: 
					if variableValues.count(v) != 1:
						print variableName + ": Variable cannot contain duplicate values"
						return False
					elif v[0] == "(" and v[-1] == ")":
						if unknownValue:
							print variableName + ": Only one value can be marked unknown"
							return False
						else:
							unknownValue = v[1:-1]
							variableValues[variableValues.index(v)] = unknownValue

				self.__variables.append(Variable(variableName, variableValues,unknownValue))			
		
		except:
			
			print "Invalid file"
			return False
		
		return True
	
		
	def createVariableModels(self):
		

		for v in self.__variables:
			
			verifyAllowActions, toAllowActions = v.getActions()
			actions = verifyAllowActions + toAllowActions
			
			transitions = []
			state_props = {}
			refinements = []

			state_props["SleepState"] = []
			
			idx = 0
			
			values = v.getValues()
			
			for value in values:
				state_transitions = []
				
				#Verifying allow transitions to the same state (value remains same) 
				state_transitions.append((idx,idx+1))
				
				#Allow transitions to other values
				for i in range (0,len(v.getValues())):
					
					if i == idx:
						continue
					
					state_transitions.append((i,len(verifyAllowActions) + 1 + i))
					
				state_props["SleepState"].append(idx)
				state_props[v.getName() + value] = [idx]
				idx += 1
				transitions.append(state_transitions)
				
			action_file = open(self.__outputDir + v.getName() + ".lsts", "w")	
			
			w = lsts.writer(action_file)
			w.set_actionnames(actions)
			w.set_transitions(transitions)
			
			w.set_stateprops(state_props)     
			w.get_header().initial_states = 0
			w.write()	
			
		
	def createInterface(self):
		
		transitions = []
		state_props = {}
		refinements = []
		actions = []
		
		state_props["SleepState"] = [0]
	

		#Add central state
		transitions.append([])
		for v in self.__variables:
			
			verifyTransitions = []
			values = v.getValues()

			
		
			for value in values:
			
				#Sets CallVerify transitions and actions
				transitions.append([])
				
				verifyTransitions.append((len(transitions)-1,self.__addAction__("REQ<@PARENT: "+ v.getName() + value + ">", actions)))
				transitions[-1].append((0,self.__addAction__("SLEEPapp<ReturnVerify" + v.getName() +":"+ value + ">", actions)))		
			
				#add setValue transitions and actions
				if ( value != v.getUnknownValue()): 
					transitions.append([])
					transitions[0].append((len(transitions)-1,self.__addAction__("WAKEapp<CallSet" + v.getName() + value + ">", actions)))

					transitions.append([])
					transitions[-2].append((len(transitions)-1,self.__addAction__("REQALL<@PARENT: To"+ v.getName() + value + ">", actions)))

					transitions[-1].append((0,self.__addAction__("SLEEPapp<ReturnSet" + v.getName() + value + ">", actions)))
				
					#Adds CallDiscovers from unknown value 
					if(v.getUnknownValue()):
		
						transitions.append([])
						transitions[0].append((len(transitions)-1,self.__addAction__("WAKEapp<@PARENT: CallDiscover" + v.getName() + value + ">", actions)))

						transitions.append([])
						transitions[-2].append((len(transitions)-1,self.__addAction__("REQ<@PARENT: "+ v.getName() + v.getUnknownValue() + ">", actions)))
						
						transitions.append([])
						transitions[-3].append((len(transitions)-1,self.__addAction__("REQ<@PARENT: "+ v.getName() + value + ">", actions)))
						
						transitions[-2].append((len(transitions)-1,self.__addAction__("REQALL<@PARENT: To"+ v.getName() + value + ">", actions)))
			
						transitions[-1].append((0,self.__addAction__("SLEEPapp<@PARENT: ReturnDiscover"+ v.getName() + value + ">", actions)))
				
			transitions.append(verifyTransitions)
			transitions[0].append((len(transitions)-1,self.__addAction__("WAKEapp<CallVerify" + v.getName() + "Status>", actions)))
			
		
		#Add forget settings call
		foundForget = False
		for v in self.__variables:
			if v.getUnknownValue():
			
				if not foundForget:
					transitions.append([])
					transitions[0].append((len(transitions)-1,self.__addAction__("WAKEapp<CallForgetSettings>", actions)))
					foundForget = True
					
				transitions.append([])
				transitions[-2].append((len(transitions)-1,self.__addAction__("REQALL<@PARENT: To" + v.getName() + v.getUnknownValue() +">", actions)))			
				
		if foundForget:
			transitions[-1].append((0,self.__addAction__("SLEEPapp<ReturnForgetSettings>", actions)))
		
	
			
		action_file = open(self.__outputDir + "interface.lsts", "w")				


		w = lsts.writer(action_file)
		w.set_actionnames(actions)
		w.set_transitions(transitions)
		
		w.set_stateprops(state_props)     
		w.get_header().initial_states = 0
		w.write()
	
	
	def __addAction__(self, actionName,actionList):
		
		if actionList.count(actionName) == 0:
			actionList.append(actionName)
			return len(actionList)
		
		else:
			return actionList.index(actionName) + 1
			
					
	
if __name__ == "__main__":

	
	#Parse command line arguments
	parser = optparse.OptionParser(usage="usage: %prog [options] input_file")
	parser.add_option("-o", "--output", dest="outdir", default=".",
			help="Output path for the generated variable models.")
	parser.add_option("-i","--interface", dest="interface", default = False, action="store_true", 
			help = "Generate a common interace model for the variables")
	outputdir = None

	#Argument parsing...
	(options, args) = parser.parse_args()

	if len(args) != 1:
		parser.error("incorrect number of arguments")
		exit(1)
		
	if not os.path.exists(args[0]):
		print "Inputfile: " + args[0] + " does not exist!"
		exit(1)

	variableFile = args[0]

	if options.outdir and not os.path.exists(options.outdir): 
		
		try:
			os.makedirs(options.outdir)
		except:
			"Error creating output directory"
			exit(1)
			
	if options.outdir[-1] != os.sep: options.outdir += os.sep
		
	v = VariableModelCreator(variableFile,options.outdir)
	if(v.readVariables()):
		v.createVariableModels()
		if options.interface:
			v.createInterface()