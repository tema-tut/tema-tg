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


# python standard:
import copy
import random

version="0.2 Coverage Language"
# 0.1 -> 0.2 'values x[,...] [in action regexp]' syntax added

# enumerations:

# Query quantifier
EQQuantifier = eqqAny, eqqAll = range(2)

# Query item types
EQItemType = eqiAction, eqiValue, eqiValueInAction, eqiSomethingElse = range(4)

# Coverage Operator
# the order must be the same as in clparser.OPERATORS
ECOperator = ecoOr, ecoAnd, ecoThen = range(3)

def _mean(list_of_nums):
    return sum(list_of_nums)/float(len(list_of_nums))

class CoverageStorage:
    def __init__(self):
        self._storagestack=[]
        
    def push(self):
        self._storagestack.append(copy.copy(self._storage))
    
    def pop(self):
        self._storage=self._storagestack.pop()
    
    def markExecuted(self,transition):
        raise NotImplementedError()


class Query(CoverageStorage):
    def __init__(self):
        CoverageStorage.__init__(self)
        self._storage={}

    def deepcopy(self,whatever=None):
        nq=Query()
        nq._storage=copy.copy(self._storage)
        nq._storagestack=copy.copy(self._storagestack)
        nq._itemtype=self._itemtype
        return nq

    def __deepcopy__(self,whatever=None):
        return self.deepcopy()
        
    # CoverageStorage interface:
    def markExecuted(self,transition):
        """
        transition is of type Model.Transition
        datamap maps variable names to chosen data values
        """
        if self._itemtype==eqiAction:
            actionstr=transition.getAction().toString()
            for act_re in self._storage:
                if act_re.match(actionstr):
                    self._storage[act_re]+=1
        elif self._itemtype==eqiValue:
            return # it's impossible to say which values were used in expressions
        else:
            raise NotImplementedError("Query supports only action item type.")

    # Query interface - for setup
    def setItemType(self,itemtype):
        if not itemtype in EQItemType:
            raise NotImplementedError("Unsupported itemtype: %s" % itemtype)
        self._itemtype=itemtype

    def setItemRegExps(self,list_of_regexp_objects):
        if not list_of_regexp_objects:
            raise ValueError("List of regexp objects is empty.")
        self._storage={}
        for re in list_of_regexp_objects:
            self._storage[re]=0

    # Query interface - needed by getPercentage in requirements:
    def max(self):
        return max(self._storage.values())

    def mean_w_ulimit(self,ulimit):
        return sum([min(v,ulimit) for v in self._storage.values()]) / float(len(self._storage))

    # Query interface - needed by getExecutionHint in requirements:
    def getExecutionHint(self, nodeSemantics):
        if nodeSemantics == eqqAny :
            distance=1
            for hits in self._storage.values():
                if hits > 0:
                    return ( set(), 0 )
            actions=set( [ alpha for alpha in self._storage.keys() ] )
            return (actions, distance)
        elif nodeSemantics == eqqAll :
            actions=set( [ alpha for alpha,cnt in self._storage.iteritems() if cnt == 0 ] )
            distance=len(actions)
            return (actions, distance)
        else:
            raise NotImplementedError("Unsupported node semantics: %s"\
                                      % nodeSemantics)

    def __str__(self):
        return "Query(itemtype=%s,storage=%s)" % (self._itemtype,self._storage)

class Requirement:
    def getPercentage(self):
        raise NotImplementedError()

    def getExecutionHint(self):
        print self
        raise NotImplementedError()

    def pickDataValue(self,set_of_possible_values):
        """data extension: coverage is able to choose a value among
        the given data values so that is affects the coverage, if
        possible.
        """
        raise NotImplementedError()

    def setParameter(self, parametername, parametervalue):
        pass

    def log(self,*args): pass

class ElementaryRequirement(CoverageStorage,Requirement):
    LOWERBOUND=1
    EXACTVALUE=2
    SETOFVALUES=3

    def __init__(self):
        CoverageStorage.__init__(self)
        self._quantifier, self._query, self._reqvalue, self._reqtype = None, None, None, None

    def deepcopy(self,whatever=None):
        er=ElementaryRequirement()
        er._quantifier,er._query,er._reqvalue,er._reqtype=(
            self._quantifier,self._query.deepcopy(),self._reqvalue,self._reqtype)
        return er

    def __deepcopy__(self,whatever):
        return self.deepcopy()
    
    # CoverageStorage interface:
    def markExecuted(self,transition):
        self._query.markExecuted(transition)

    def push(self):
        self._query.push()
        
    def pop(self):
        self._query.pop()

    # Requirement interface:
    
    def getPercentage(self):
        if self._quantifier==eqqAny:
            return self._query.max()/self._reqvalue
        elif self._quantifier==eqqAll:
            return self._query.mean_w_ulimit(self._reqvalue)/self._reqvalue
        else:
            raise NotImplementedError("Unsupported quantifier: %s\n")

    def getExecutionHint(self):
        return self._query.getExecutionHint(self._quantifier)

    def pickDataValue(self,set_of_possible_values):
        if self._reqtype!=ElementaryRequirement.SETOFVALUES or not self._reqvalue:
            # this object does not require covering data or all required values
            # have been covered
            return None
        str_possible_values=set(str(v) for v in set_of_possible_values)
        intersection=self._reqvalue.intersection(str_possible_values)
        if intersection:
            chosen_value=random.choice(tuple(intersection))
            self._reqvalue.remove(chosen_value)
            # Whenever a value is returned, it is assumed that the
            # value will really be used! so it is already marked as
            # covered. The reason is that based on the string given to
            # markExecuted it is almost impossible to quess which
            # values were actually chosen.
            self._query._storage[chosen_value]+=1
            if self._quantifier==eqqAny:
                self._reqvalue=set() # one covered => all covered
            return chosen_value
        else:
            return None

    # ElementaryRequirement interface:
    def setQuery(self,query_object):
        self._query=query_object

    def setLowerBoundRequirement(self,quantifier,reqvalue):
        if not reqvalue:
            raise ValueError("Required value cannot be zero.")
        self._quantifier=quantifier
        self._reqvalue=float(reqvalue)
        self._reqtype=ElementaryRequirement.LOWERBOUND

    def setValueCoverageRequirement(self,quantifier,reqvalues):
        self._reqvalue=set(reqvalues)
        self._quantifier=quantifier
        self._reqtype=ElementaryRequirement.SETOFVALUES

    def __str__(self):
        return "ElementaryRequirement(reqval=%s,reqtype=%s,quant=%s,query=%s)" % \
               (self._reqvalue,self._reqtype,self._quantifier,self._query)


class CombinedRequirement(CoverageStorage,Requirement):
    def __init__(self,operator=None,requirements=None):
        self._operator=operator
        if not requirements: self._requirements=[]
        else: self.setRequirements(requirements)

    def deepcopy(self,whatever=None):
        cr=CombinedRequirement(self._operator)
        cr._requirements=[r.deepcopy() for r in self._requirements]
        return cr

    def __deepcopy__(self,whatever=None):
        return self.deepcopy()

    # coverage storage interface --- pass through the commands to
    # sub requirements
    
    def markExecuted(self,transition):
        if self._operator in [ ecoAnd, ecoOr ]:
            # AND & OR -> every unfilled req gets mark
            for r in self._requirements:
                if r.getPercentage()<1:
                    r.markExecuted(transition)
        elif self._operator == ecoThen:
            # THEN -> only the first unfilled req gets mark
            for r in self._requirements:
                if r.getPercentage()<1:
                    r.markExecuted(transition)
                    break

    def push(self):
        for r in self._requirements: r.push()

    def pop(self):
        for r in self._requirements: r.pop()

    # requirement interface:

    def getPercentage(self):
        if self._operator==ecoAnd:
            # return min( [r.getPercentage() for r in self._requirements] )
            # THIS CAUSES MODULE TESTS TO FAIL, BUT GIVES BETTER GUIDANCE:
            return _mean( [r.getPercentage() for r in self._requirements] )
        elif self._operator==ecoOr:
            return max( [r.getPercentage() for r in self._requirements] )
        elif self._operator==ecoThen:
            return _mean( [r.getPercentage() for r in self._requirements] )
        else:
            raise TypeError("Operator in CombinedRequirements was '%s'!" % operator)

    def getExecutionHint(self):
        actions=set()
        distance=-1
        if self._operator == ecoThen:
            distance=0
            for a,d in [ r.getExecutionHint() for r in self._requirements]:
                if distance == 0:
                    actions = a
                distance += d
        elif self._operator==ecoAnd:
            distance=0
            for a,d in [ r.getExecutionHint() for r in self._requirements]:
                distance+=d
                actions = actions | a
        elif self._operator==ecoOr:
            for a,d in [ r.getExecutionHint() for r in self._requirements]:
                actions = actions | a
                if distance < 0 or distance > d:
                    distance=d
        else:
            pass
        return (actions,distance)

    def pickDataValue(self,set_of_possible_values):
        for r in self._requirements:
            chosen_value=r.pickDataValue(set_of_possible_values)
            if chosen_value:
                return chosen_value
    
    # combined requirement interface:
        
    def setOperator(self,operator):
        if not operator in ECOperator:
            raise ValueError("Operator %s not in %s" % (operator,ECOperator))
        self._operator=operator
    
    def addRequirement(self,requirement):
        self._checkrequirement(requirement)
        self._requirements.append(requirement)

    def setRequirements(self,list_of_reqs):
        for requirement in list_of_reqs:
            self._checkrequirement(requirement)
        self._requirements=list_of_reqs

    def _checkrequirement(self,r):
        if not isinstance(r,Requirement):
            raise ValueError("%s is not Requirement object" % r)
