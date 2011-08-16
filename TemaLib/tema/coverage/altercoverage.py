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
AlterCoverage reads the following parameter values:

- tabulistsizepercentage (natural number, default: 30)
  
  size of tabu list related to the total amount of actions in each application

- maxnumofswitches (natural number, default: 10000)
  
  maximum number of application switches that will be executed - 
  this is used just as a divider for calculating the current coverage 
  percentage
"""


import tema.coverage.coverage as coverage
import copy
import re
import random

class ElementaryRequirement:
    def __init__(self, actionREs, tabuListSizePercentage):
    
        # self._storage is a dictionary with action regular expessions as keys.
        # The value for each expression tells if that action has been executed recently, 
        # it is incremented each time the action is executed and decremented when the action
        # is removed from tabu list.
        
        # actionREs is a list -> reads each expression separately to self._storage      
        if isinstance(actionREs, list):
            self._storage = { }
            for regExp in actionREs:
                self._storage[regExp] = 0
                
        # actionREs is a dictionary
        elif isinstance(actionREs, dict):
            self._storage = actionREs
            
        else:
            raise Exception, 'altercoverage.ElementaryRequirement: actionREs needs to be a list or dictionary of regular expressions'
                
        self._storageStack = []
        
        # Tabu list contains indices to recently executed actions.       
        self._tabuList = []
        self._tabuListStack = []
        self._tabuListSize = int(len(self._storage) * (tabuListSizePercentage / 100.0))
        
        self.allExecutions = copy.copy(self._storage)
        
    def setTabuListSizePercentage(self, tabuListSizePercentage):
        self._tabuListSize = int(len(self._storage) * (tabuListSizePercentage / 100.0))
                
    def deepcopy(self,whatever=None):
        nq = ElementaryRequirement(self._storage, self._tabuListSize)
        nq._storageStack = copy.copy(self._storageStack)
        
        nq._tabuList=copy.copy(self._tabuList)
        nq._tabuListStack=copy.copy(self._tabuListStack)

        return nq

    def __deepcopy__(self,whatever=None):
        return self.deepcopy()
        
    def push(self):
        self._storageStack.append(copy.copy(self._storage))
        self._tabuListStack.append(copy.copy(self._tabuList))
            
    def pop(self):
        self._storage=self._storageStack.pop()
        self._tabuList=self._tabuListStack.pop()  
        
    def getExecutionHint(self):
        
        actions = set( [ alpha for alpha,cnt in self._storage.iteritems() if cnt == 0 ] )
        distance = len(actions)
        return (actions, distance)   

    def markExecuted(self,transition):
    
        progress = False

        actionStr = transition.getAction().toString()
        
        for actionRE in self._storage:
        
            # if action matches, increment storage value to the action, and
            # add it to tabu list
            if actionRE.match(actionStr):
                self._storage[actionRE]+=1

                self._tabuList.append(actionRE)
                
                if self._storage[actionRE] == 1:
                    # signs that progress has been made in this application
                    progress = True
                    
                if len(self._storageStack) == 0:
                    self.allExecutions[actionRE]+=1
                        
        # removes oldest values from tabu list if its size exceeds max tabulist size
        while len(self._tabuList) > self._tabuListSize:
            # pops action from tabu list and decreases the corresponding storage value
            actionRE = self._tabuList.pop(0)
            self._storage[actionRE]-=1
                           
        return progress   
                        
# default values for AlterCoverage parameters

# defines how many actions are stored in each elementary requirement's tabu list
DEFAULT_TABU_LIST_SIZE_PERCENTAGE = 30

# maximum number of application switches that will be executed - 
# this is used just as a divider for calculating the current coverage percentage
DEFAULT_MAX_NUM_OF_SWITCHES = 10000

# creates and returns AlterCoverage requirement object
def requirement(req, model):
    # initialises the random number generator
    random.seed()
    
    # req should be a string containing application names + parameters
    # splitting it to pieces
    apps = req.split()
    
    # the last word tells the size of combinations that will be tested 
    combinationParameter = apps.pop()     
   
    # message for parameter error
    PARAM_MESSAGE = 'Error in parameters. Parameters for altercoverage are: list of applications; \
an integer between 2 and the number of applications, specifying the size of combinations to test or \'random\' for random application switches; \
eg. \'FileManager Gallery Contacts 2\' or \'FileManager Gallery Contacts random\''

    # Creates AlterCoverage
    coverage = AlterCoverage()

    # elementary requirements
    coverage.elemReqs = []
    coverage.elemReqIndicesStack = []
    
    coverage.setElementaryRequirements(model, apps, DEFAULT_TABU_LIST_SIZE_PERCENTAGE)   
    
    # current elementary requirement - index to elemReqIndices
    coverage.i = 0    
    coverage.iStack = []  
    
    # number of application switches done and max number of switches
    coverage.numOfSwitchesDone = 0    
    coverage.numOfSwitchesDoneStack = [] 
    coverage.maxNumOfSwitches = DEFAULT_MAX_NUM_OF_SWITCHES
    
    
    if combinationParameter == 'random':
        # random combinations
        coverage.isRandomCombinations = True
        
        # stores index of each application to the testing sequence and shuffles it
        coverage.elemReqIndices = range(len(coverage.elemReqs))
        random.shuffle(coverage.elemReqIndices)
        
    else:
        # creates a testing sequence for each possible application switch for the given sized combinations
        
        # converts combinationParameter into integer
        try:
            sizeOfCombinations = int(combinationParameter)
        except ValueError:
            sizeOfCombinations = 0

        if sizeOfCombinations < 2 or sizeOfCombinations > len(coverage.elemReqs):
            raise Exception, PARAM_MESSAGE

        coverage.isRandomCombinations = False
        
        # index for each application
        requirementIndices = range(len(coverage.elemReqs))             

        # Creates combination sequence
        coverage.elemReqIndices = createCombinationSequence(requirementIndices, sizeOfCombinations)

    return coverage
    
def createCombinationSequence(requirementIndices, sizeOfCombinations):
    combinationsList = []
    combinationsOfCurrent = []        
    indexOfFirst = 0           
    
    # generateCombinations is used to get all application combinations of the given size, 
    # eg. [0,1,2], [0,2,1], [1,0,2]...
    # These combinations are asked one at a time from the generator, and based on them is 
    # created a combinationsList in which the first cell contains 
    # all combinations starting with the first index, and so on,
    # eg. [[[0, 1, 2], [0, 2, 1]], [[1, 2, 0], [1, 0, 2]], ...
    for i in generateCombinations(requirementIndices, sizeOfCombinations):
        if i[0] != indexOfFirst:
            combinationsList.append(combinationsOfCurrent)
            indexOfFirst = i[0]
            combinationsOfCurrent = []
            
        combinationsOfCurrent.append(i)
                        
    combinationsList.append(combinationsOfCurrent)
    
    # Finally, elemReqIndices is formed based on combinationsList
    # elemReqIndices is a sequential chain of indices, which defines the order in which applications will be switched, 
    # containing each possible switch
    # eg.  [2, 1, 0, 2, 1, 0, 2, 0, 1, 2, 0, 1, 2]
            
    elemReqIndices = [combinationsOfCurrent[-1][0]]
            
    while len(combinationsOfCurrent) != 0:
        combination = combinationsOfCurrent.pop()
        elemReqIndices.extend(combination[1:])
        combinationsOfCurrent = combinationsList[combination[-1]]
        
    return elemReqIndices
    
# generates all n sized combinations from items
def generateCombinations(items, n):
    if n == 0: 
        yield []
    else:
        for i in range(len(items)):
            for cc in generateCombinations(items[i+1:] + items[:i], n-1):
                yield [items[i]] + cc  
    


# AlterCoverage class
# this should not be created directly, use requirement function or AlterCoverage.deepcopy
class AlterCoverage(coverage.Requirement) :
    
    def __init__(self):
        pass
        
    def setParameter(self, parametername, parametervalue):
        if not parametername in ['tabulistsizepercentage','maxnumofswitches']:
            print __doc__
            raise Exception("Invalid parameter '%s' for altercoverage." % parametername)

        if parametername=='tabulistsizepercentage':
            if parametervalue < 0.0 or parametervalue > 100.0:
                raise Exception('Invalid parameter \'tabulistsizepercentage\' value for altercoverage. \
\'tabulistsizepercentage\' is a percentage defining the size of tabu list related to the total amount of actions in each application, \
and therefore its value has to be between 0.0 and 100.0')

            for elemReq in self.elemReqs:
                elemReq.setTabuListSizePercentage(parametervalue)
                
        elif parametername=='maxnumofswitches':
            self.maxNumOfSwitches = parametervalue
            
    def __deepcopy__(self,whatever=None):
    
        cov = AlterCoverage()
        
        cov.isRandomCombinations = self.isRandomCombinations

        cov.elemReqs = copy.deepcopy(self.elemReqs)
        cov.elemReqIndices = copy.copy(self.elemReqIndices)
        cov.elemReqIndicesStack = copy.copy(self.elemReqIndicesStack)

        cov.i = self.i
        cov.iStack = copy.copy(self.iStack)
        
        cov.numOfSwitchesDone = self.numOfSwitchesDone
        cov.numOfSwitchesDoneStack = copy.copy(self.numOfSwitchesDoneStack)
        cov.maxNumOfSwitches = self.maxNumOfSwitches
                
        return cov
        
    def push(self):
        for elemReq in self.elemReqs:
            elemReq.push()
            
        self.elemReqIndicesStack.append(copy.copy(self.elemReqIndices))
        self.iStack.append(copy.copy(self.i))
        self.numOfSwitchesDoneStack.append(copy.copy(self.numOfSwitchesDone))
        
    def pop(self):
        for elemReq in self.elemReqs:
            elemReq.pop()
            
        self.elemReqIndices = self.elemReqIndicesStack.pop()
        self.i = self.iStack.pop()
        self.numOfSwitchesDone = self.numOfSwitchesDoneStack.pop()
                
    # sets coverage requirements according to given application names
    def setElementaryRequirements(self, model, apps, tabuListSize) :
        for app in reversed(apps):

            pattern = app + ".*:start_aw.*"
            
            # asks all matching actions from the model 
            appActions = model.matchedActions([re.compile(pattern)])
                        
            # turns actions into regular expression objects
            appActionREs = [ re.compile(alpha) for alpha in appActions ]              
                        
            # Creates an ElementaryRequirement based on the regular expressions 
            # and tabu list size.
            elemReq = ElementaryRequirement(appActionREs, tabuListSize)
            self.elemReqs.append(elemReq)
                                     
    def getPercentage(self):
        return float(self.numOfSwitchesDone) / self.maxNumOfSwitches

    # returns execution hint from the current elementary requirement
    def getExecutionHint(self):
        return self.__getCurrentElementaryRequirement().getExecutionHint()
        
    def markExecuted(self, transition):           
        
        curElemReq = self.__getCurrentElementaryRequirement()
        progress = False

        # marks transition executed for each elementary requirement
        for elemReq in self.elemReqs:
        
            # return value of the current elementary requirement is what
            # decides if progress has been made
            if elemReq == curElemReq:
                progress = elemReq.markExecuted(transition)
            else:
                elemReq.markExecuted(transition)
                                                                     
        if progress:
            self.__stepIndex()
            
            for elemReq in self.elemReqs:
                actionsTotal = len(elemReq.allExecutions)
                executedActions = 0
                for value in elemReq.allExecutions.values():
                    if value > 0:
                        executedActions += 1
                                        
                #print 'proportion of actions executed at least once: ' + str(float(executedActions)/actionsTotal)
 
                        
    def __getCurrentElementaryRequirement(self):
        return self.elemReqs[self.elemReqIndices[self.i]]

    def __stepIndex(self):
        self.numOfSwitchesDone += 1
        self.i += 1

        if self.i == len(self.elemReqIndices):
            # end of indices - starts over
            self.i = 0
            
            # randomises the order of indices if doing random combinations
            if self.isRandomCombinations:
                random.shuffle(self.elemReqIndices)

