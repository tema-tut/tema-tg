#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
Lsts model object hierarchy and a conversion tool to turn kendo product into a lstsmodel object.

"""

from tema.ats4appmodel.kendomodel import *

import os
import re
import shutil
from optparse import OptionParser

import tema.lsts.lsts as lsts

import urllib



### some utility functions ###

def escape(line):
    
    #line = line.replace(" ", "%20")
    #line = line.replace("\\", "%5C")
    #return line.replace("/", "%2F") 
    return urllib.quote(line)
    
    
def getModelName(product):
    
    parent = product
    modelName = escape(product.getName());
    
    while parent.getParentProduct() and parent.getParentProduct().getName() != "System model":
        parent = parent.getParentProduct()
        
    if parent and parent != product:
        modelName = escape(parent.getName() + " - " + product.getName());
    
    return modelName

###################################    
        
        
class LstsModel:
    
    def __init__(self):
        self.__states = []
        self.__transitions = []
        self.__actions = []
        self.__start_state = None

    def getStates(self):
        return self.__states
    
    def setStart_state(self, state):
        self.__start_state = state

    def getStart_state(self):
        return self.__start_state

    def setStates(self, value):
        self.__states = value   

    def addState(self, state):
       self.__states.append(state)

    def addTransition(self, transition):
        self.__transitions.append(transition)

    def getActions(self):
        return self.__actions
    
    def addAction(self, action_name, refinements):
        #check if action already exists
        for a in self.__actions:
            if a.getName() == action_name:
                return a
        
        new_action = Action(action_name, refinements)
        self.__actions.append(new_action)
        return new_action
    
    def removeState(self, state):
        if state in self.__states:
            self.__states.remove(state)


class StateProposition:

    def __init__(self, name, keywords):
        self.__name = name
        self.__keywords = keywords


    def getName(self):
        return self.__name


    def getKeywords(self):
        return self.__keywords


    def setName(self, value):
        self.__name = value


    def setKeywords(self, value):
        self.__keywords = value

        
    def addKeyword(self, kw):
        self.__keywords.append(kw)
        

class LstsTransition:
    
    def __init__(self, action, fromState, toState):
        self.__action = action
        self.__fromState = fromState
        self.__toState = toState

    def setFromState(self, value):
        self.__fromState = value

    def setToState(self, value):
        self.__toState = value

    def getToState(self):
        return self.__toState

    def getFromState(self):
        return self.__fromState

    def setAction(self, action):
        self.__action = action
        
    def getAction(self):
        return self.__action

 

class LstsState:
    
    def __init__(self):
        self.__state_propositions = []
        self.__transitions = []

    def setState_propositions(self, sps):
        self.__state_propositions = sps

    def addState_proposition(self, sp):
        self.__state_propositions.append(sp)
    
    def getState_propositions(self):
        return self.__state_propositions
    
    def addKeyword(self, sp):
        self.__state_propositions.append(sp)
    
    def addTransition(self, transition):
        self.__transitions.append(transition)
        
    def getTransitions(self):
        return self.__transitions
    
    def setTransitions(self, transitions):
        self.__transitions = transitions
        
  
class Action:
    
    def __init__(self, name, refinements):
        
        self.__name = name
        self.__refinements = refinements


    def getName(self):
        return self.__name


    def getRefinements(self):
        return self.__refinements


    def setName(self, value):
        self.__name = value


    def setRefinements(self, value):
        self.__refinements = value


        
class LstsModelCreator:
    
    APP_MODEL = "APP_MODEL"
    SYS_MODEL = "SYS_MODEL"
    SUB_MODEL = "SUB_MODEL"
    

    
    def __init__(self, product,allProducts):
        self.__product = product
        self.__allProducts = allProducts
        self.__lsts_model = LstsModel()
        self.__generate_ts = False
        self.__stateMapper = {}


    def convertProduct(self, generate_ts = False, generateSleep = False, defaultSleep = False):
        
        self.__generate_ts = generate_ts
        
        states = []
        #Mapping of kendo state ids to the lsts states are saved to the id_index dictionary
        self.__stateMapper = {}
        
        sleepState = StateProposition("SleepState", None)
        
        gates = []
        
        #Create an lsts state for each kendo state
        for s in self.__product.getStates():
            
            #in gates are not added as independent states. Instead, they are later combined to the initial state
            if not s.getType() == "IN_GATE": #and not s.getType() == "OUT_GATE":
                
                #if s.getKeywords():
                if s.getType() == "APP_MODEL" or s.getType() == "SUB_MODEL":
                    name = s.getName()
                else: name = s.getEvent_id()
                    
                if s.getType() == "SYSTEM_STATE":  
                    svName = "sv" + name
                else: svName = name
                 
                sv = StateProposition(svName, s.getKeywords())
                    
                lsts_state = LstsState()
                lsts_state.addState_proposition(sv)
                
                if s.getLinkedProduct():
                    lsts_state.addState_proposition(sleepState)
                
                states.append(lsts_state)
                
                id = s.getId()
                self.__stateMapper[id] = lsts_state
                
                #TODO: check if both can and cannotsleep are given.
                if generateSleep and s.getType() == "SYSTEM_STATE":
                    if s.getDescription().find("CanSleep") != -1 or (defaultSleep == True and s.getDescription().find("CanNotSleep") == -1):
                    
                        #TODO: remove. 5800 model dependant!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        """
                        menuOpen = False
                        for t in self.__product.getTransitions():
                        
                            if menuOpen:
                                break
                                
                            if t.getToState() !=s:
                                continue
                            
                            if not t.getKeywords():
                                break
                                
                            for kw in t.getKeywords():
                                if kw.find("text_softkey_option"):
                                    menuOpen = True
                                    break
                            break
                            
                        if menuOpen:
                            continue
                        """
                        
                        sleepts_state = LstsState()
                        #sleepts_state.addState_proposition(sv)
                        sleepts_state.addState_proposition(sleepState)
                        states.append(sleepts_state)
                        
                        
                        sleepts = self.__lsts_model.addAction("SLEEPts", None)
                        toSleepTranstion = LstsTransition(sleepts,lsts_state,sleepts_state)
                        lsts_state.addTransition(toSleepTranstion)
                        
                        wakets = self.__lsts_model.addAction("WAKEts",None)
                        toWakeTransition = LstsTransition(wakets,sleepts_state,lsts_state)
                        sleepts_state.addTransition(toWakeTransition)
           
            else:
                gates.append(s)
                    
        start_state = states[0]
        
        #Find the entry points ( start states ) of this model.
        #sub models have entry points and system/app models has a start state.
        entry_points = [s for s in self.__product.getStates() if s.getType() == "ENTRY_POINT" or s.getType() == "START_STATE" ]
        exit_points = [s for s in self.__product.getStates() if s.getType() == "EXIT_POINT" ]
        #Common initial state is generated for sub and appmodels:
        if len(entry_points) > 1 or len(exit_points) > 0:
            start_state = LstsState()
            states.append(start_state)
            start_state.addState_proposition(sleepState)

            #create wakepapp transitions from the common initial state to the entry point states for sub models.
            for e in entry_points:
            
                if self.__generate_ts and e.getType() == "START_STATE":
                    actionName = "WAKEts"
                else:   
                    actionName = "WAKEapp<" + str(self.__product.getName()) + ":" + e.getEvent_id() + ">"

                action = self.__lsts_model.addAction(actionName, None)                
                lstsTransition = LstsTransition(action, start_state, self.__stateMapper[e.getId()])
                start_state.addTransition(lstsTransition)
        
        #System models that are directly converted (no taskswitcher) need additional WAKEts-transition before the actual start state
        #elif not generate_ts and len(exit_points) == 0:
        #    start_state = LstsState()
        #    states.append(start_state)
        #    action = self.__lsts_model.addACtion("WAKEts",None)
        #    lstsTransition = LstsTransition(action, start_state, self.__stateMapper[entry_points[0].getId()])
        #    start_state.addTransition(lstsTransition)
            
        
        #Merge InGates to inital state
        for bill in gates:
            self.__stateMapper[bill.getId()] = start_state
        

        self.__lsts_model.setStart_state(start_state)
        self.__lsts_model.setStates(states)
        
        #Process the states and their transitions
        for s in self.__product.getStates():
            
            state = self.__stateMapper[s.getId()]
            
            #Sleep transitions to the initial state are added to exit points for avoiding deadlocks
            if s.getType() == "EXIT_POINT":
                
                #Exit from a sub/app model ( transition to exit-point, port name is found from event_id)
                #Sleep transition is bound to the initial state of the app/sub model
    
                if self.__generate_ts and entry_points[0].getType() == "START_STATE":
                    actionName = "SLEEPts"
                else:  
                    #Create a normal transition to the exit point
                    actionName = "SLEEPapp<" + str(self.__product.getName()) + ":" + s.getEvent_id() + ">"
                action = self.__lsts_model.addAction(actionName, None)
                
                lstsTransition = LstsTransition(action, state, start_state)
                state.addTransition(lstsTransition)
                
                #Exit point has no transitions, so continue.
                continue             
            
            #Prosess the leaving transitions of this state.
            for t in self.__product.getTransitions():         
                
                if s.getId() == t.getFromState().getId():
                    
                    if re.match("in\d+|out\d+", t.getFromPort()) and self.__generate_ts: continue
                    
                    #If the transition ends to the first state of the model (after start_state),
                    #the transtion is attached to the start_state of the model, because in kendo
                    #keywords that are defined in start state are executed always when entering the first state.
                    if t.getToState().getEvent_id() =="S1" and len(entry_points) == 1 and s.getType() != "START_STATE" and s.getType() != "ENTRY_POINT":
                        to_state = self.__stateMapper[entry_points[0].getId()] #TODO: Certain that id 1 is always the start state?
                    else:
                        to_state = self.__stateMapper[t.getToState().getId()]
                    
                    self.__processTransition(t,state, to_state)
                    
                    
        return self.__lsts_model

    def __addAction(self, state, action_name, targetState = None, refinements = None):

        if action_name == None: return state
        
        action = self.__lsts_model.addAction(action_name, refinements)
        
        #if the given action already exists in the state ( multiple transitions to InGate situations),
        #the two states are merged
        for transition in state.getTransitions():
            if transition.getAction() == action:
                return transition.getToState()
        
        target = None
        if targetState != None:
            target = targetState
        else:
            target = LstsState()
            self.__lsts_model.addState(target)
            
        
        lsts_transition = LstsTransition(action, state, target)
        state.addTransition(lsts_transition)
        
        return target
    
    
    def __getWakeAction(self, transition):

        #return from sub/app model:
        if transition.getFromState().getLinkedProductId():
            #transition from linked model through port in system level:
            if re.match("out\d+|in\d+",transition.getFromPort()):
                #actionName = "WAKEapp<fromProduct" + str(transition.getFromState().getLinkedProductId()) + "Port" + transition.getFromPort() + ">"
                actionName = "WAKEapp<from " + transition.getFromState().getLinkedProduct().getName() + ":" + transition.getFromPort() + ">"
                
            #Task switcher transition to application model
            elif self.__generate_ts and transition.getFromState().getType()=="APP_MODEL":
                actionName ="SLEEPts<" + escape(transition.getFromState().getName()) + ">"
            
            else:
                #prod_id = str(transition.getFromState().getLinkedProductId())
                #actionName = "WAKEapp<Product" + prod_id + "Port" + transition.getFromPort() + ">"
                prod_name = transition.getFromState().getLinkedProduct().getName()
                actionName = "WAKEapp<" + prod_name + ":" + transition.getFromPort() + ">"
                
            
            return actionName
        
        #Initial state of a model.
        elif transition.getFromState().getType() == "ENTRY_POINT" or transition.getFromState().getType() == "START_STATE" :
            
            entry_points = [s for s in self.__product.getStates() if s.getType() == "ENTRY_POINT" or s.getType() == "START_STATE" ]
            exit_points = [s for s in self.__product.getStates() if s.getType() == "EXIT_POINT" ]
            
            #Start or entry state of an app/sub model
            if len(entry_points) > 1 or len(exit_points) > 0:
                actionName = "--transition from entry point"
                return actionName
            
            #Only one entry point, generate wakeapp
            #else:                               
            #    actionName = "WAKEapp<Product" + str(product.getId()) + "Port" + transition.getToState().getEvent_id() + ">"
            #    return actionName
            

            #Start state of a system model.
            elif len(exit_points) == 0:
                
                if self.__generate_ts:
                    return None
                        
                return "WAKEts"
                    
        
        #port transition
        elif transition.getFromState().getType() == "OUT_GATE" or transition.getFromState().getType() == "IN_GATE":
            
            #actionName = "WAKEapp<toProduct" + str(self.__product.getId()) + "Port" + transition.getFromState().getEvent_id() +">"
            actionName = "WAKEapp<to" + self.__product.getName() + ":" + transition.getFromState().getEvent_id() +">"
            
            return actionName 
        
        return None
        
    
    def __getSleepAction(self, transition):
        
        actions = []
        #transition to sub/app model
        if transition.getToState().getLinkedProductId() or (self.__generate_ts and transition.getToState().getType() =="APP_MODEL"):
            
            #transition between linked models through port in system level:
            if re.match("out\d+|in\d+",transition.getToPort()):
                #actionName = "SLEEPapp<toProduct" + str(transition.getToState().getLinkedProductId()) + "Port" + transition.getToPort() + ">"
                actionName = "SLEEPapp<to" + transition.getToState().getLinkedProduct().getName() + ":" + transition.getToPort() + ">"
            
                        #Task switcher transition from application model
            elif self.__generate_ts and transition.getToState().getType()=="APP_MODEL":
                actionName ="WAKEtsCANWAKE<" + escape(transition.getToState().getName()) + ">"

            
            #Normal transition to linked model
            else: 
                #actionName = "SLEEPapp<Product" + str(transition.getToState().getLinkedProductId()) + "Port" + transition.getToPort() + ">"
                actionName = "SLEEPapp<" + transition.getToState().getLinkedProduct().getName() + ":" + transition.getToPort() + ">"
            
            return actionName
        
        #transition to port:        
        elif transition.getToState().getType() == "OUT_GATE" or transition.getToState().getType() == "IN_GATE" :
            
            #actionName = "SLEEPapp<fromProduct" + str(self.__product.getId()) + "Port" + transition.getToState().getEvent_id() +">"
            actionName = "SLEEPapp< from" + self.__product.getName() + ":" + transition.getToState().getEvent_id() +">"
            return actionName 
        
        return None
    
    
    def __getAwAction(self,transition,state):
        #transition has or could have keywords.
        if transition.getKeywords() != None or (transition.getFromPort() == "DEFAULT_EXIT" and transition.getFromState().getType() != "START_STATE" and transition.getFromState().getType() != "ENTRY_POINT"):                 
            #actionName = "awFrom" + str(transition.getFromState().getEvent_id()) + "To" + str(transition.getToState().getEvent_id()) + "Via" + str(transition.getEvent_id()) 
            actionName = "aw" + str(transition.getEvent_id()) 
            return actionName
        
        #If the start state has keywords, this is turned into an action word,
        #because it needs to be run every time the start state is entered
        elif len(state.getState_propositions()) > 0 and state.getState_propositions()[0].getName() == "Start":

            #if len(state.getState_propositions()[0].getKeywords()) == 0 and not self.__generate_ts:
            #    return None
            
            #actionName = "awFrom" + str(transition.getFromState().getEvent_id()) + "To" + str(transition.getToState().getEvent_id()) + "Via" + str(transition.getEvent_id()) 
            actionName = "aw" + str(transition.getEvent_id()) 
            return actionName
               
        return None
    
    
    def __getActivityActions(self, transition):
        
        actions = []
        
        if not transition.getActivities():
            return None
        
        for act in transition.getActivities():
                            
            if act.getType() == "SET_FLAG_VALUE":
                              
                reg_value = "toEnabled"
                if act.getValue() == "false":
                    reg_value = "toDisabled"
                
                actionName = "REQALL<"+reg_value + act.getKey()+ ">"
                actions.append(actionName)
        
        if len(actions) == 0:
            return None
        return actions
    
    
    def __getConditionActions(self,transition):
        
        if transition.getGuard_conditions() != None and len(transition.getGuard_conditions()) > 0:
                        
            reg_value = "Enabled"
            if transition.getGuard_conditions()[0].getReg_value() == "false":
                reg_value = "Disabled"
            
            actionName = "REQ<"+reg_value+ transition.getGuard_conditions()[0].getKey()+ ">"
            return actionName
        
        return None
   
   
    def __processTransition(self, kendo_transition, from_lsts_state, to_lsts_state):
       
        sleepState = StateProposition("SleepState",None)
       
        #Every Kendo transition is transformed into a series of Tema transitions
        condAct = self.__getConditionActions(kendo_transition)
        wakeAct = self.__getWakeAction(kendo_transition)   
        aw = self.__getAwAction(kendo_transition,from_lsts_state)
        activities = self.__getActivityActions(kendo_transition)             
        sleepAct =  self.__getSleepAction(kendo_transition)
        
        last_state = from_lsts_state
        
        if condAct:
            
            if not wakeAct and not aw and not activities and not sleepAct:
                last_state = self.__addAction(last_state, condAct, targetState = to_lsts_state )
            else:
                last_state = self.__addAction(last_state, condAct )
        
        if wakeAct:
            
            #Add Sleepts for wakets transitions. WAKEts is the first transition in system model when using direct conversion
            #In these cases, a new start state is created before the kendo start state, where WAKEts and SLEEPts transitions are bound
            if wakeAct == "WAKEts":
                start_state = LstsState()
                self.__lsts_model.addState(start_state)
                self.__lsts_model.setStart_state(start_state) 
                self.__addAction(start_state, wakeAct, targetState = last_state)
                                
                action = self.__lsts_model.addAction("SLEEPts", None)
                lsts_transition = LstsTransition(action, to_lsts_state, start_state)
                to_lsts_state.addTransition(lsts_transition)
                
            else:
                if not aw and not activities and not sleepAct:
                    self.__addAction(last_state, wakeAct, targetState = to_lsts_state)
                else:
                    last_state = self.__addAction(last_state, wakeAct)
        
        if aw:
            
            keywords = kendo_transition.getKeywords()
            if from_lsts_state.getState_propositions()[0].getName() == "Start":
                keywords = from_lsts_state.getState_propositions()[0].getKeywords()  
            #Create empty refinement
            if keywords == None:
                keywords = []
            
            if not activities and not sleepAct:   
                self.__addAction(last_state, aw, to_lsts_state, keywords)
            else:
                last_state = self.__addAction(last_state, aw, refinements = keywords)
        
        if activities:
            for act in activities[:-1]:
                previous_state = last_state
                last_state = self.__addAction(last_state, act)
            
            if not sleepAct:
                self.__addAction(last_state, activities[-1], targetState = to_lsts_state)
            else:
                last_state = self.__addAction(last_state, activities[-1])
            
        if sleepAct:
            
            if re.match("WAKEtsCANWAKE<.*>",sleepAct):
                
                wake_state = LstsState()
                self.__lsts_model.addState(wake_state)
                action = self.__lsts_model.addAction(sleepAct, None)
                lsts_transition = LstsTransition(action, last_state, wake_state)
                last_state.addTransition(lsts_transition)
                
                sleepAct = "WAKEtsWAKE<" + escape(kendo_transition.getToState().getName()) + ">"
                last_state = wake_state

            last_state = self.__addAction(last_state, sleepAct, targetState = to_lsts_state)                   
            to_lsts_state.addState_proposition(sleepState)                       
        
        
    
    def convertToTaskSwitcher(self, apps_only,  gate_model_name):
        
        if not apps_only:
            self.convertProduct(generate_ts = True)
        else:
            self.__convertAppsOnlyTaskSwitcher()
  
        gate_state = LstsState()
        self.__lsts_model.addState(gate_state)
        
        for from_state in self.__product.getStates():
            
            #If apps only ts has been created, state mapper does not contain all states of the system model
            if not from_state.getId() in self.__stateMapper:
                continue
            
            from_lsts_state = self.__stateMapper[from_state.getId()]
            
            if from_state.getType() == "APP_MODEL":
                
                for to_state in self.__product.getStates():
                    
                    if to_state.getType() != "APP_MODEL": continue
                    if from_state == to_state: continue
                     
                    to_lsts_state = self.__stateMapper[to_state.getId()]
                    
                    action_name = "ACTIVATED<" + getModelName(to_state.getLinkedProduct()) +">"
                    action = self.__lsts_model.addAction(action_name,None)
                    lsts_transition = LstsTransition(action, from_lsts_state, to_lsts_state)
                    from_lsts_state.addTransition(lsts_transition)
                
                #Add "ACTIVATED" transition to the port model and back"
                action_name = "ACTIVATED<" + gate_model_name +">"
                action = self.__lsts_model.addAction(action_name,None)
                lsts_transition = LstsTransition(action, from_lsts_state, gate_state)
                from_lsts_state.addTransition(lsts_transition)
                
                action_name = "ACTIVATED<" + getModelName(from_state.getLinkedProduct()) +">"
                action = self.__lsts_model.addAction(action_name,None)
                lsts_transition = LstsTransition(action, gate_state, from_lsts_state)
                gate_state.addTransition(lsts_transition)
 
 
            #sub-models
            if from_state.getLinkedProduct():
                
                submodels = []
                submodels.append(from_state.getLinkedProduct())
                states = []
                states.extend(from_state.getLinkedProduct().getStates())
                
                while True: 
                    
                    substates = []
                    for state in states:  
                        if state.getLinkedProduct():
                            submodels.append(state.getLinkedProduct())
                            substates.extend(state.getLinkedProduct().getStates())
                            
                    states = substates
                    if len(states) == 0: break
             
                for sub in submodels:
                    
                    action_name = "ACTIVATED<" + getModelName(sub) +">"
                    action = self.__lsts_model.addAction(action_name,None)
                    lsts_transition = LstsTransition(action, from_lsts_state, from_lsts_state)
                    from_lsts_state.addTransition(lsts_transition)
                

        return self.__lsts_model
        
        
    def __convertAppsOnlyTaskSwitcher(self):
        
        ###Generates simple taskswitcher based on the application models in the system model. All other transition/system
        ###states are omitted.
        initial_state = LstsState()
        self.__lsts_model.addState(initial_state)
        
        self.__lsts_model.setStart_state(initial_state)
        
        self.__stateMapper = {}
        app_states = []

        #Create WAKEtsCANWAKE, awActivate, WAKEtsWAKE, SLEEPts loop.
        for state in self.__product.getStates():
            
            if state.getType() =="APP_MODEL":
                
                app_states.append(state)
                
                action_name = "WAKEtsCANWAKE<" + escape(state.getName()) +">"
                action = self.__lsts_model.addAction(action_name, None)
                
                toState = LstsState()
                self.__lsts_model.addState(toState)
                
                lsts_transition = LstsTransition(action, initial_state, toState)
                initial_state.addTransition(lsts_transition)
                
                fromState = toState
                action_name = "awActivate<" + escape(state.getName()) +">" 
                appName = state.getName()
                for p in self.__allProducts:
                    if state.getLinkedProductId() == p.getId():
                        matcher = re.search("[aA]ppname:\\s*\"(\\w+)\"",p.getDescription())
                        if matcher != None:
                            appName = matcher.group(1)
                        break
                    
                
                action = self.__lsts_model.addAction(action_name, ["kw_LaunchApp §".decode("iso-8859-1")  + appName + "§".decode("iso-8859-1") ])
                
                toState = LstsState()
                self.__lsts_model.addState(toState) 
                lsts_transition = LstsTransition(action, fromState, toState)
                fromState.addTransition(lsts_transition)
                
                fromState = toState
                action_name = "WAKEtsWAKE<" + escape(state.getName()) +">" 
                action = self.__lsts_model.addAction(action_name,None)
                
                toState = LstsState()
                self.__lsts_model.addState(toState) 
                lsts_transition = LstsTransition(action, fromState, toState)
                fromState.addTransition(lsts_transition)
                toState.addState_proposition(StateProposition(state.getName() + " running", None))
                self.__stateMapper[state.getId()] = toState
                
                fromState = toState
                action_name = "SLEEPts<" + escape(state.getName()) +">" 
                action = self.__lsts_model.addAction(action_name, None)
                
                lsts_transition = LstsTransition(action, fromState, initial_state)
                fromState.addTransition(lsts_transition)
                
        
        for state in app_states:         
            for kendo_transition in self.__product.getTransitions():
                if state.getId() == kendo_transition.getFromState().getId():
                    if re.match("in\d*|out\d*",kendo_transition.getFromPort()):
                        self.__processTransition(kendo_transition, self.__stateMapper[state.getId()], self.__stateMapper[kendo_transition.getToState().getId()])
        
            """
            for to_state in app_states:
                if state == to_state: continue
                from_lsts_state = self.__stateMapper[state.getId()]
                to_lsts_state = self.__stateMapper[to_state.getId()]
                
                action_name = "ACTIVATED<" +to_state.getName().replace(" ", "%20") +">"
                action = self.__lsts_model.addAction(action_name,None)
                lsts_transition = LstsTransition(action, from_lsts_state, to_lsts_state)
                from_lsts_state.addTransition(lsts_transition)
            """    

        return self.__lsts_model 

                           
    def createGateModel(self, system_model):
        
        gate_model = LstsModel()
        initial_state = LstsState()
        gate_model.addState(initial_state)
        gate_model.setStart_state(initial_state)

        for transition in system_model.getTransitions():
            if re.match("in\d+|out\d+", transition.getFromPort()):
                #actionName = "WAKEapp<fromProduct" + str(transition.getFromState().getLinkedProductId()) + "Port" + transition.getFromPort() + ">"
                actionName = "WAKEapp< from" + transition.getFromState().getLinkedProduct().getName() + ":" + transition.getFromPort() + ">"
                
                action = gate_model.addAction(actionName,None)
                
                wake_state = None
                #check if the given wake already exists (multiple transitions to one InGate) 
                for t in initial_state.getTransitions():
                    if t.getAction() == action:
                        wake_state =  t.getToState()
                
                if not wake_state:
                    
                    wake_state = LstsState()
                    gate_model.addState(wake_state)
                    lsts_transition = LstsTransition(action,initial_state,wake_state)
                    initial_state.addTransition(lsts_transition)
                
                #actionName = "SLEEPapp<toProduct" + str(transition.getToState().getLinkedProductId()) + "Port" + transition.getToPort() + ">"
                actionName = "SLEEPapp<to" + transition.getToState().getLinkedProduct().getName() + ":" + transition.getToPort() + ">"
                
                action = gate_model.addAction(actionName,None)
                
                lsts_transition = LstsTransition(action,wake_state,initial_state)
                wake_state.addTransition(lsts_transition)
        
        return gate_model
        
