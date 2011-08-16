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
Kendo xml -model class hierarchy and parser.

Provides classes for different parts of kendo models 
(states, transitions, products, flags...)

Provides a parser class (KendoXMLParser) to read kendo xml-file and to
produce an object hierarchy from it.

"""

from xml.dom import minidom
import os
import re
        
class KendoProduct:
    
    """
    Class for kendo products ( Application models and sub models)
    
    """
    
    
    def __init__(self):
        self.__states = []
        self.__transitions = []
        self.__id = None
        self.__parentProduct = None
        self.__name = ""
        self.__description = ""
        self.__subModels = []
       
    
    def printData(self):
        """
        Prints out the product information (states, transitions,...)
        """
        
        print "Product Id: " + str(self.__id) + " name: " + self.__name
        
        print "States:"
        for s in self.__states:
            print "\t",
            s.printData()
            
        print "Transitions:"
        for t in self.__transitions:
            t.printData()
            print ""
        

    def getStateById(self, id):
        for state in self.__states:
            if state.getId() == id:
                return state

    def getStates(self):
        return self.__states

    def getTransitions(self):
        return self.__transitions

    def getId(self):
        return self.__id
    
    def getName(self):
        return self.__name

    def setName(self, value):
        self.__name = value

    def setStates(self, value):
        self.__states = value

    def setTransitions(self, value):
        self.__transitions = value

    def setId(self, value):
        self.__id = value

    def addState(self, state):
       self.__states.append(state)

    def addTransition(self, transition):
        self.__transitions.append(transition)
        
    def getParentProduct(self):
        return self.__parentProduct

    def getModelFileName(self):
        return self.__modelFileName

    def setParentProduct(self, value):
        self.__parentProduct = value

    def setModelFileName(self, value):
        self.__modelFileName = value

    def addSubModel(self,model):
        self.__subModels.append(model)
        
    def getSubModels(self):
        return self.__subModels
        
    def setDescription(self, desc):
        self.__description = desc 
        
    def getDescription(self):
        return self.__description
    
    name = property(getName, setName, None, None)


class SystemProduct(KendoProduct):
    
    """
    Derived Product class for system models. In addition to base product information,
    system model contains application models.
    """
    
    def __init__(self):
        KendoProduct.__init__(self)
        self.__appModels = []
        
    
    def addAppModel(self,model):
        self.__appModels.append(model)
        
    def getAppModels(self):
        return self.__appModels
    
        

class KendoState:
    
    """
    Class for kendo system event related information
    """
    
    def __init__(self, id, name, desc, type, event_id, linkedProductId, keywords):
        
        self.__id = id
        self.__type = type
        self.__name = name
        self.__event_id = event_id
        self.__linkedProductId = linkedProductId
        self.__keywords = keywords
        self.__linkedProduct = None
        self.__description = desc


    def printData(self):
        print "State Id: " + str(self.__id) + " name: " + self.__name + " type: " + self.__type 
        

    def getId(self):
        return self.__id

    def getType(self):
        return self.__type

    def getName(self):
        return self.__name

    def getLinkedProductId(self):
        return self.__linkedProductId

    def getLinkedProduct(self):
        return self.__linkedProduct

    def setId(self, value):
        self.__id = value

    def setType(self, value):
        self.__type = value

    def setName(self, value):
        self.__name = value

    def setLinkedProductId(self, value):
        self.__linkedProductId = value

    def setLinkedProduct(self, value):
        self.__linkedProduct = value
        
    def getEvent_id(self):
        return self.__event_id

    def setEvent_id(self, value):
        self.__event_id = value
    
    def setKeywords(self, kws):
        self.__keywords = kws 
        
    def getKeywords(self):
        return self.__keywords
    
    def addKeyword(self, kw):
        self.__keywords.append(kw)
        
    def setDescription(self, desc):
        self.__description = desc 
        
    def getDescription(self):
        return self.__description

class KendoTransition:
    
    """
    Class for kendo user event related information
    
    """

    def __init__(self, id, name, event_id, keywords, toState, fromState, toPort, fromPort, activities, guard_conditions):
        self.__id = id
        self.__toState = toState
        self.__fromState = fromState
        self.__name = name
        self.__keywords = keywords
        self.__toPort = toPort
        self.__fromPort = fromPort
        self.__event_id = event_id
        self.__activities = activities
        self.__guard_conditions = guard_conditions



    def printData(self):
        print "\tTransition Id: " + str(self.__id) + " name: " + self.__name
        print "\tFrom State: " + str(self.__fromState.getId()) + ", port: " + self.__fromPort,
        print "to state: " + str(self.__toState.getId()) + ", port: " + self.__toPort 
        
        if self.__keywords:
            if len(self.__keywords) > 0:
                print "\tKeywords:"
                
            for k in self.__keywords:
                print "\t\t" + k.encode("utf-8")
            
    def getToState(self):
        return self.__toState

    def getFromState(self):
        return self.__fromState

    def getName(self):
        return self.__name

    def getKeywords(self):
        return self.__keywords

    def setToState(self, value):
        self.__toState = value

    def setFromState(self, value):
        self.__fromState = value

    def setName(self, value):
        self.__name = value

    def setKeywords(self, value):
        self.__keywords = value
    
    def addKeword(self, kw):
        self.__keywords.append(kw)
        
    def getToPort(self):
        return self.__toPort

    def getFromPort(self):
        return self.__fromPort

    def setToPort(self, value):
        self.__toPort = value

    def setFromPort(self, value):
        self.__fromPort = value
        
    def setActivities(self, activities):
        self.__activities = activities
        
    def getActivities(self):
        return self.__activities

    def getId(self):
        return self.__id
    
    def setId(self, id):
        self.__id = id
        
    def getEvent_id(self):
        return self.__event_id

    def getGuard_conditions(self):
        return self.__guard_conditions

    def setGuard_conditions(self, value):
        self.__guard_conditions = value
        
        

class KendoActivity:

    """
    Class for kendo activities (enable/disable actions, ...) 
    
    """

    def __init__(self):
        self.__value = None
        self.__type = None
        self.__key = None
    
    def __init__(self, value, type, key):
        self.__value = value
        self.__type = type
        self.__key = key
        
    def setValue(self, value):
        self.__value = value
    
    def getValue(self):
        return self.__value
      
    def setType(self, type):
        self.__type = type
    
    def getType(self):
        return self.__type
       
    def setKey(self, key):
        self.__key = key
    
    def getKey(self):
        return self.__key
    

class KendoFlag:
    """
    
    """

    def __init__(self, default_value, description, name):
        self.__name = name
        self.__description = description
        self.__default_value = default_value


    def getName(self):
        return self.__name

    def getDescription(self):
        return self.__description

    def getDefault_value(self):
        return self.__default_value

    def setName(self, value):
        self.__name = value

    def setDescription(self, value):
        self.__description = value

    def setDefault_value(self, value):
        self.__default_value = value


class GuardCondition:
    """
    """

    def __init__(self, type, reg_value, key):
        self.__type = type
        self.__reg_value = reg_value
        self.__key = key


    def getType(self):
        return self.__type

    def getReg_value(self):
        return self.__reg_value

    def getKey(self):
        return self.__key

    def setType(self, value):
        self.__type = value

    def setReg_value(self, value):
        self.__reg_value = value

    def setKey(self, value):
        self.__key = value


class TestData:

    def __init__(self,logicalName,description,items):
        self.__logicalName = logicalName
        self.__description = description
        self.__items = items
    
    def getLogicalName(self):
        return self.__logicalName

    def getDescription(self):
        return self.__description
        
    def getItems(self):
        return self.__items
        
    def setLogicalName(self, value):
        self.__logicalName = value

    def setDescription(self, value):
        self.__description = value
        
    def setItems(self,value):
        self.__items = value
    

class TestDataItem:

    def __init__(self,name,path,result,priority):
        self.__name = name
        self.__path = path
        self.__result = result
        self.__priority = priority
    
    def getName(self):
        return self.__name

    def getPath(self):
        return self.__path
        
    def getResult(self):
        return self.__result

    def getPriority(self):
        return self.__priority
    
    def setName(self, value):
        self.__name = value

    def setPath(self, value):
        self.__path = value
        
    def setResult(self, value):
        self.__result = value

    def setPriority(self, value):
        self.__priority = value


class UseCaseModel:

    def __init__(self,usecases):
        self.__useCases = usecases
    
    def getUseCases(self):
    
        return self.__useCases

    def addUseCase(usecase):
    
        if self.__useCases == None:
            self.__useCases = []
    
        self.__useCase.append(useCase)


class UseCase:

    def __init__(self,name, description, paths):
        self.__paths = paths
        self.__name = name
        self.__description = description
        
    def getPaths(self):
        return self.__paths
        
    def getName(self):
        return self.__name

    def setName(self, value):
        self.__name = value
        
    def getDescription(self):
        return self.__description 

    def setDescription(self, value):
        self.__description = value



class UseCasePath:

    def __init__(self,name,description, transitions):
        self.__transitions = transitions
        self.__name = name
        self.__description = description
        
    def getTransitions(self):
        return self.__transitions
        
    def getName(self):
        return self.__name

    def setName(self, value):
        self.__name = value
        
    def getDescription(self):
        return self.__description
        
    def setDescription(self, value):
        self.__description = value
        

class KendoXMLParser:
    
    """
    Class for parsing kendo xml models to an object hierachy. 
     
    Class can be used to parse whole kendo model projects, which includes
    an XML-file for the system model and application models in a subfolder <system_model>.xml.dat/apps/
    If the <model>.xml.dat/apps/ folder is not found, the model is considered to be an separate application model
    and is parsed correspondingly.
    """
    
    def __init__(self, sysModelPath):
        self.__products = []
        self.__sysModelFile = sysModelPath
        #TODO: Are flags definitely always system model level 
        self.__flags = []
        self.__testData = []
        self.__useCaseModel = None


    def getProducts(self):
        return self.__products
    
    
    def getFlags(self):
        return self.__flags


    def getTestData(self):
        return self.__testData
        
    def getUseCaseModel(self):
        return self.__useCaseModel


    def parseKendoModel(self):     
        
        #if len(file.name.rsplit(os.sep, 1)) > 1:
        #    self.__modelDir = file.name.rsplit(os.sep, 1)[0]
        
        appModelDirectory = self.__sysModelFile + ".dat" + os.sep + "apps" + os.sep
        try:
            root, dirs, files = os.walk(appModelDirectory).next()
        except:
            root, dirs, files = None,[],[]
        
        appModelFiles = []
        for file in files:
            if re.match(".*\.xml", file):
                appModelFiles.append(file)
        
        if not self.__parseKendoProduct(self.__sysModelFile, None):
            print ("Invalid system model")
            return False;
        
        
        #Parse flags from the system model
        try:
            xml = minidom.parse(self.__sysModelFile)
            flags = xml.getElementsByTagName("flag")
            
            for flag in flags:
                name = flag.attributes.getNamedItem("name").value
                description = flag.attributes.getNamedItem("description").value
                default_value = flag.attributes.getNamedItem("default_value").value == "true"
                kFlag = KendoFlag(default_value, description, name)
                self.__flags.append(kFlag)
            
            self.__addReturnTransitionToPorts()
        except:
            print "Invalid system model"
            return False

        #Parse use cases from the system model:
        try:
            useCases = []
            for ucmodel in xml.getElementsByTagName("UseCaseModel"):
                useCaseNodes = ucmodel.getElementsByTagName("UseCase")
                for uc in useCaseNodes:
                    useCasePaths =[]
                    ucName = uc.attributes.getNamedItem("name").value
                    ucDesc = uc.attributes.getNamedItem("description").value
                    paths = uc.getElementsByTagName("UseCasePath")
                    for path in paths:
                        pathName = path.attributes.getNamedItem("name").value
                        pathDesc = path.attributes.getNamedItem("description").value
                        transitions = path.getElementsByTagName("transition")
                        ucTransitions = []
                        for trans in transitions:
                            transModel = trans.attributes.getNamedItem("modelName").value
                            transId = int(trans.attributes.getNamedItem("id").value)
                            ucTransitions.append((transModel,transId))
                        
                        useCasePaths.append(UseCasePath(pathName,pathDesc,ucTransitions))
                    useCases.append(UseCase(ucName,ucDesc,useCasePaths))
                
            self.__useCaseModel = UseCaseModel(useCases)
        
        except:
            print "Invalid system model"
            return False
        
        for appModel in appModelFiles:
            if not self.__parseKendoProduct(root + os.sep + appModel, self.__products[0]):
                print "Invalid application model: " + appModel
                return False;
           
        
        for product in self.__products:
            for state in product.getStates():
                if state.getLinkedProductId():
                    for linked_prod in self.__products:
                        if linked_prod.getId() == state.getLinkedProductId():
                            state.setLinkedProduct(linked_prod)
                            linked_prod.setParentProduct(product)
                            break
                
        #Read test data
        if not self.__parseTestData():
            print "Invalid test data"
            return False
        
        return True
        
    
    def __parseTestData(self):
    
        try:
            testDataDir = self.__sysModelFile + ".dat" + os.sep + "TestData" + os.sep
            
            try:
                root, dirs, files = os.walk(testDataDir).next()
            except:
                root, dirs, files = None,[],[]
            
            testDataFiles = []
            for file in files:
                if re.match(".*\.xml", file):
                    testDataFiles.append(file)
            

            for file in testDataFiles:
                xml = minidom.parse(testDataDir + os.sep + file)
                dataEntities = xml.getElementsByTagName("TestData")
                for data in dataEntities:
                    logicalName = data.getElementsByTagName("logicalName")[0].lastChild.nodeValue
                    try:
                        desc = data.getElementsByTagName("description")[0].lastChild.nodeValue
                    except:
                        desc = ""
                    items = data.getElementsByTagName("TestDataItem")
                    testDataItems = []
                    for item in items:
                        itemName = item.getElementsByTagName("name")[0].lastChild.nodeValue
                        try:
                            path = item.getElementsByTagName("path")[0].lastChild.nodeValue
                        except:
                            path = ""
                        
                        try:
                            result = item.getElementsByTagName("result")[0].lastChild.nodeValue
                        except:
                            result = ""
                            
                        try:
                            priority = item.getElementsByTagName("priority")[0].lastChild.nodeValue
                        except:
                            priority = ""
                        
                        testDataItems.append(TestDataItem(itemName,path,result,priority))
                    
                    self.__testData.append(TestData(logicalName,desc,testDataItems))
        
        except:
            return False
        
        return True

    def printKendoModel(self):
        
        for p in self.__products:
            p.printData()        
        #self.__products[0].printData()
        
        
    def __parseKendoProduct(self, xmlPath, parentProduct):    
        
        try:
        
            xml = minidom.parse(xmlPath)
            products = xml.getElementsByTagName("product")
            first_product = None
            parent = parentProduct
            for product in products:
                
                if parent:
                    kendoProduct = KendoProduct()
                else:
                    parent = product
                    kendoProduct = SystemProduct()
                
                productId = int(product.attributes.getNamedItem("id").value)
                productName = product.attributes.getNamedItem("name").value
                
                try:
                    productDesc = product.getElementsByTagName("description")[0].lastChild.nodeValue
                except:
                    productDesc =""
                    
                kendoProduct.setDescription(productDesc)
                kendoProduct.setId(productId)
                kendoProduct.setName(productName)
                
                states = product.getElementsByTagName("state")
                transitions = product.getElementsByTagName("transition")
                
                #Parse states
                for state in states:
                    
                    id = int(state.attributes.getNamedItem("id").value)
                    type = state.getElementsByTagName("type")[0].lastChild.nodeValue
                    
                    try:
                        name = state.getElementsByTagName("name")[0].lastChild.nodeValue
                    except:
                        name = ""
                    
                    event_id = state.getElementsByTagName("event_id")[0].lastChild.nodeValue
                    try:
                        desc = state.getElementsByTagName("description")[0].lastChild.nodeValue
                    except:
                        desc = ""
                    try:
                        linkedModelId = int(state.getElementsByTagName("linkedModelId")[0].lastChild.nodeValue)
                    except:
                        linkedModelId = None
                            
                     
                    #Read keywords 
                    keywords = []
                    kws = state.getElementsByTagName("keyword")
                    for kw in kws:
                        keywordType = kw.attributes.getNamedItem("type").value
                        keywordParams = kw.attributes.getNamedItem("parameter").value
                        keywords.append(keywordType + " " + keywordParams)
                        
                    kendoState = KendoState(id, name, desc, type, event_id, linkedModelId, keywords)
                    
                    kendoProduct.addState(kendoState)
                
                #Parse transitions
                for transition in transitions:
                    
                    id = int(transition.attributes.getNamedItem("id").value)
                    
                    event_id = transition.attributes.getNamedItem("event_id").value
                    
                    try:
                        name = state.getElementsByTagName("name")[0].lastChild.nodeValue
                    except:
                        name = ""
                    
                    toStateId = int(transition.attributes.getNamedItem("to").value)
                    fromStateId = int(transition.attributes.getNamedItem("from").value)
                    
                    toPort = transition.attributes.getNamedItem("toport").value
                    fromPort = transition.attributes.getNamedItem("fromport").value
                    
                    
                    if transition.getElementsByTagName("keywords") == None or len(transition.getElementsByTagName("keywords")) == 0:
                        keywords = None
                    else:    
                        #Read keywords 
                        keywords = []
                        kws = transition.getElementsByTagName("keyword")
                        for kw in kws:
                            keywordType = kw.attributes.getNamedItem("type").value
                            keywordParams = kw.attributes.getNamedItem("parameter").value
                            keywords.append(keywordType + " " + keywordParams)
                      
                    #Read activities
                    activities = []
                    acts = transition.getElementsByTagName("activity")
                    for act in acts:
                        
                        actValue = act.attributes.getNamedItem("value").value
                        actType = act.attributes.getNamedItem("type").value
                        actKey = act.attributes.getNamedItem("key").value
                        
                        kendoAct = KendoActivity(actValue, actType, actKey)
                        activities.append(kendoAct)
                        
                    #Read guard conditions
                    guard_conditions = []
                    conditions = transition.getElementsByTagName("condition")
                    for cond in conditions:
                        
                        condType = cond.attributes.getNamedItem("type").value
                        condRegVal = cond.attributes.getNamedItem("required_value").value
                        cond = cond.attributes.getNamedItem("key").value
                        
                        condition = GuardCondition(condType, condRegVal, cond)
                        guard_conditions.append(condition)
        
                    toState = kendoProduct.getStateById(toStateId)
                    fromState = kendoProduct.getStateById(fromStateId)
                                                                             
                    kendoTransition = KendoTransition(id, name, event_id, keywords, toState, fromState, toPort, fromPort, activities, guard_conditions)
                    kendoProduct.addTransition(kendoTransition)
                if first_product == None:
                    first_product = kendoProduct
                    if parentProduct:
                        parentProduct.addAppModel(kendoProduct)
                else:
                    first_product.addSubModel(kendoProduct)
                               
                self.__products.append(kendoProduct)       
            return True
        
        except:

            return False
    
            
         #Function adds return transitions for outgoing port transitions
    def __addReturnTransitionToPorts(self):
        
        
        for p in self.__products:
            
            newTransitions = []
            
            #returnStates = []
            
            #KendoState(None, "returnFromIn", type, event_id, linkedProductId, keywords)
                        
            for transition in p.getTransitions():
                if transition.getToPort() and re.match("in\d+", transition.getToPort()):
                    
   
                    #States and ports are mirrored
                    toState = transition.getFromState()
                    fromState = transition.getToState()
                    toPort = transition.getFromPort()
                    fromPort = transition.getToPort()
                
                    #TODO: which id?
                    newTrans = KendoTransition(None, "return", None , None, toState, fromState, toPort, fromPort, None, None)
                    newTransitions.append(newTrans)
                    
            for n in newTransitions:
                p.addTransition(n)
