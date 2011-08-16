

"""
findnewcoverage tries to find new things in the model.

findnewcoverage can be used with weightguidance, gameguidance, or any guidance
that uses either Requirement.getPercentage() or findnewcoverages own
transitionPoints() method to guide itself.

The "thing" or things findcoverage is trying to find is specified in the
req string given to requirement() function.

--- Examples of req strings:

Find new action words:
"findnew aw"

Set the size of the aw tabulist. To only remember 100 latest action words:
"findnew aw[tabusize:100]"

Find new keyword or new state:
"findnew kw or state"

Set weights for requirements, here keywords are 2x more valuable than states.
Also, only remember the 100 latest states.
"findnew kw[weight:2] or state[weight:1,tabusize:100]"

Find new actionword-stateproposition pairs:
"findnew aw while stateprop"

Find new action-stateproposition pairs and also new states:
('while' binds stronger than 'or')
"findnew aw while stateprop or state"

Parameters for the whole action-stateprop pair go after while:
"findnew aw while[tabusize:100] stateprop"

Find new ("state-wise unique") switches between apps A and B:
"findnew switch[apps:A B]"

Find new transitions of model components whose name contains Calendar:
"findnew componenttransition[model:model.ext,components:.*Calendar.*]

-----

Common parameter names (accepted by all the reqs):
tabusize:
    The size of the tabulist, ie. how many items the requirement remembers.
    If tabusize=100 and the 101th item is found, the first one is forgotten,
    and if the first one is found again, it will be considered new again.
    Either a natural number or "infinite" (default: "infinite").
weight:
    The "value" of finding a new such item. Only relevant when there are more
    than one items connected with "or".
    Weight is either a number or "decreasing" (default: "decreasing").
    "decreasing" = 1/(N+1) where N is the number of items found so far.
    Only weightguidance understands custom weights, gameguidance etc. ignore em.


Single reqs::
aw:
    action words (unique by name)
kw:
    keywords (unique by name)
state:
    unique states
transition:
    unique transitions = (source_state,action,dest_state)
stateprop:
    unique state propositions
switch:
    "state-wise" unique switches from one application to other.
    Special required params:
        apps:App1 App2 ...
            The apps we're trying to switch between.
            The appnames must contain the device name(??). Eg. "MyPhone/App1".
componenttransition:
    unique transitions of the given model components.
    Special params:
        (either give both 'model' and 'components',
         or neither to search for all the component transitions)
        model:MODELFILENAME
            The parallel composition model, eg. target/combined-rules.ext
        components:C1 C2 ...
            the component names, whitespace-separated, may be regexp,
            eg. .*Switcher.* Note that the component names must be in the
            same format as in the model file, so there may be some device etc.
            stuff in front of the actual model name, eg. DeviceX/rm/ModelName
...


"""

version = "0.0003"

import re
from tema.coverage.tabulist import TabuList
from tema.coverage.coverage import Requirement, CombinedRequirement, ecoAnd

def requirement(req, model=None):
    """ Returns a TabuRequirement object based on the req string.
    """
    if hasattr(requirement,"log"):
        TabuRequirement.log = requirement.log

    try:
        tabuTitle,tabuStr = req.split(None,1) # if no space, raises ValueError
        if tabuTitle.lower() != "findnew":
            raise ValueError("findnewcoverage req should start with 'findnew '")
    except ValueError:
        raise ValueError("Invalid tabu string: '%s'" % req)

    return TabuRequirement(tabuStr)


_PARAM_PATTERN = r"(?:\[([^\]]*)\])?"

_OR_PATTERN = r"\s+or\s*" + _PARAM_PATTERN + r"\s+"
_RE_OR = re.compile(_OR_PATTERN, re.I)

# accepting 'and' as 'while', for now...
_WHILE_PATTERN = r"\s+(?:while)|(?:and)\s*" + _PARAM_PATTERN + r"\s+"
_RE_WHILE = re.compile(_WHILE_PATTERN, re.I)

_SINGLE_PATTERN = r"\s*([^\s\[]+)\s*" + _PARAM_PATTERN + r"\s*"
_RE_SINGLE = re.compile(_SINGLE_PATTERN, re.I)

class TabuRequirement(Requirement,object):
    """ """

    def __new__(cls,tabuStr,unused=None):

        # TODO: improve parsing, parentheses, etc.

        if _RE_OR.search(tabuStr):
            return object.__new__(OrTabuRequirement)

        if _RE_WHILE.search(tabuStr):
            return object.__new__(WhileTabuRequirement)

        if _RE_SINGLE.match(tabuStr):
            return SingleTabuRequirement.__new__(cls,tabuStr)

        raise ValueError("Invalid tabu string: '%s'" % tabuStr)

    def __init__(self,paramStr):
        # default params:
        self.setParameter("weight","decreasing")
        self._tabuList = TabuList()
        # user-given params:
        self.setParameterStr(paramStr)

    def setParameterStr(self,paramStr):
        if not paramStr:
            return
        for pair in paramStr.split(","):
            name,value = pair.split(":",1)
            self.setParameter(name,value)

    def setParameter(self,name,value):
        name = name.lower()
        if name in ("size","tabusize"):
            self._tabuList = TabuList( _parseSize(value) )
        elif name == "weight":
            if value in ("decreasing","decr"):
                self.weight = self._decreasingWeight
            else:
                self.weight = lambda: 1
        elif name == "name":
            self._name = value
        else:
            print __doc__
            raise ValueError(
                "Invalid param '%s' for %s"%(name,self.__class__.__name__))

    def getPercentage(self):
        """ Doesn't actually return "coverage" per se, but is a function that's
            getting closer and closer to 1 as new items are found.
            This means that the more items have been found,
            the less a new one improves coverage.
        """
        # the usual python floats have precision of ~16 digits,
        # -> tabulist sizes up to 16**10, so precision shouldn't be a problem
        return 1 - 1.0/(self._tabuList.lenUnique()+1)

    def getExecutionHint(self):
        raise NotImplementedError()

    def markExecuted(self,transition):
        # if using filterRelevant instead of filterNew, this would work a bit
        # differently in the case of a limited size tabulist.
        # not sure which is the best. see findnewcoverage_test.py.
        for item in self.filterNew(transition):
            #if self._tabuList._pushLevel == 0:
            #    self.log("FOUND: %s" % (item,))
            self._tabuList.add(item)


    # subclasses must implement filterRelevant
    # this is the func that yields all the things in the transition that
    # the TabuRequirement is interested in. (eg. aw for aw-requirement, etc.)
    def filterRelevant(self,transition):
        raise NotImplementedError()

    def filterNew(self,transition):
        """ yields all the new things found by executing the transition """
        for item in self.filterRelevant(transition):
            if item not in self._tabuList:
                yield item

    def filterOld(self,transition):
        for item in self.filterRelevant(transition):
            if item in self._tabuList:
                yield item

    def transitionPoints(self,transition):
        """ how many points executing this transitition gives.
            point = (number of new items) * weight
        """
        p = 0
        for item in self.filterNew(transition):
            p += 1
        return p * self.weight()

    def weight(self):
        return self._weight

    def _decreasingWeight(self):
        return 1.0/(self._tabuList.lenUnique()+1)

    def push(self):
        self._tabuList.push()

    def pop(self):
        self._tabuList.pop()


class SingleTabuRequirement(TabuRequirement):
    """ a single tabu requirement.
    the type is specified in the tabustring given to constructor."""

    def __new__(cls,tabuStr):
        typeStr,paramStr = _RE_SINGLE.findall(tabuStr)[0]
        if typeStr == "switch":
            return object.__new__(SwitchTabuRequirement)
        elif typeStr == "componenttransition":
            return object.__new__(ComponentTransitionTabuRequirement)
        else:
            # a simple, non-special SingleTabuRequirement whose filter
            # is simply determined by the type (no need for extra params).
            return object.__new__(SingleTabuRequirement)

    def __init__(self,tabuStr):
        typeStr,paramStr = _RE_SINGLE.findall(tabuStr)[0]
        self._name = typeStr.strip().lower()
        self._tabuFilter = tabuFilterByType(self._name)
        TabuRequirement.__init__(self,paramStr)

    def filterRelevant(self,transition):
        return self._tabuFilter(transition)



class ComponentTransitionTabuRequirement(SingleTabuRequirement):
    """Finds new transitions of given model components.

    findnew componenttransition[model:MODELFILE,components=COMPONENTNAMES]
    MODELFILE = The parallel composition model, eg. target/combined-rules.ext
    COMPONENTNAMES = The names of the model components whose transitions we
                     are searching.
    """
    def __init__(self,tabuStr):
        self._model = None
        self._components = []
        SingleTabuRequirement.__init__(self,tabuStr)

    def setParameter(self,name,value):
        if name == "components":
            self._components = value.strip().split()
            self._createFilter()
        elif name == "model":
            self._model = value
            self._createFilter()
        else:
            SingleTabuRequirement.setParameter(self,name,value)

    def _createFilter(self,raiseIfFails=False):
        if self._model and self._components:
            # Assumes that:
            #  N first rows of _model file are the components in the parallel
            #  composition. (Only) these rows match _RE_COMPONENT_FILE.
            #  The components are in the same order as in the parallel state id.
            #  These rows tell the name of model component file (relative to
            #  the dir of model file).
            #  The model component files contain "Transition_cnt = XX" line.
            #  + propably something else...
            import os.path
            compFiles = {} # key: the index in parallel composition
            _RE_COMPONENT_FILE = re.compile('([^()=]*)="([^()]*)"')
            # the component filenames are relative to this path:
            modeldir = os.path.dirname(self._model)

            f = open(self._model)
            try:
                for num, line in enumerate(f):
                    match = _RE_COMPONENT_FILE.match(line)
                    if not match:
                        break
                    compname,filename = match.groups()
                    for comp in self._components:
                        if re.match(comp+"$",compname):
                            self.log("Searching for transitions of component %i: %s" % (num,compname,))
                            compFiles[num] = os.path.join(modeldir,filename)
                            break # each component only once
            finally:
                f.close()

            # finding out the total num of transitions from component files
            numTrans = 0
            for num,filename in compFiles.iteritems():
                cf = open(filename)
                try:
                    inHeader = False
                    for line in cf:
                        li = line.strip().lower()
                        if inHeader:
                            if li.startswith("transition_cnt"):
                                numTrans += int(li.rsplit(None,1)[-1])
                                break
                            elif li.startswith("end header"):
                                raise IOError(
                                    "No Transition_cnt in '''%s'''" % (
                                    filename,))
                        elif li.startswith("begin header"):
                            inHeader = True
                finally:
                    cf.close()
            self._numTrans = numTrans

            compIndices = [i for i in compFiles.iterkeys()]
            self._tabuFilter = createComponentTransitionFilter(compIndices)
        else:
            # either 'model' or 'components' param is not given.
            # no need to panic yet, since the missing param may be coming.
            self._tabuFilter = createUndefinedFilter("componenttransition "\
                "needs both 'model' and 'components' params! (or neither to "\
                "find transitions of every component).")

    def getPercentage(self):
        return float(self._tabuList.lenUnique()) / self._numTrans



class OperatorTabuRequirement(TabuRequirement):
    """ OperatorTabuRequirement delegates the push/pop/markExecuted/...
        calls to its children reqs.
    """
    def markExecuted(self,transition):
        TabuRequirement.markExecuted(self,transition)
        for r in self._requirements:
            r.markExecuted(transition)

    def push(self):
        for r in self._requirements:
            r.push()
        TabuRequirement.push(self)

    def pop(self):
        for r in self._requirements:
            r.pop()
        TabuRequirement.pop(self)




class OrTabuRequirement(OperatorTabuRequirement):
    """ req1 or req2
        The coverage is improved if either req1 or req2 is improved.
    """

    def __init__(self, tabuStr):
        r1,paramStr,r2 = _RE_OR.split(tabuStr,1)
        self._requirements = [TabuRequirement(t) for t in [r1,r2]]
        self._name = "OR"
        TabuRequirement.__init__(self,paramStr)

    def filterRelevant(self, transition):
        """ Yields pairs (i,item), where item is something yielded by a filter
            of a req whose index is i.
        """
        for i,req in enumerate(self._requirements):
            for item in req.filterRelevant(transition):
                thatReqsItem = (i,item)
                yield thatReqsItem

    def transitionPoints(self, transition):
        return sum([r.transitionPoints(transition) for r in self._requirements])


class WhileTabuRequirement(TabuRequirement):
    """ req1 while req2
        The coverage is improved if req1 and req2 are improved at the same time
        (= on the same transition execution).
    """

    def __init__(self, tabuStr):
        r1,paramStr,r2 = _RE_WHILE.split(tabuStr,1)
        self._requirements = [TabuRequirement(r) for r in [r1,r2]]
        self._name = "WHILE"
        TabuRequirement.__init__(self,paramStr)

    def filterRelevant(self, transition):
        """ Yields all the possible tuples of the form (y1,y2,...) where
        y1 is something yielded by the filter of my first requirement,
        and so on.

        Eg. if my reqs were "action" and "stateprop", I would yield
        all the action-stateprop pairs.
    """
        startsOfTuples = [ () ]
        for r in self._requirements:
            oneLongerStartsOfTuples = []
            for sot in startsOfTuples:
                for x in r.filterRelevant(transition):
                    oneLongerStartsOfTuples.append( sot+(x,) )
            startsOfTuples = oneLongerStartsOfTuples
        # they're full tuples now
        for t in startsOfTuples:
            yield t


class SwitchTabuRequirement(SingleTabuRequirement):
    """ switch[apps:A B C] """
    def __init__(self, tabuStr):
        typeStr,paramStr = _RE_SINGLE.findall(tabuStr)[0]
        self._fromApp = None
        self._fromState = None
        self._fromStack = []
        SingleTabuRequirement.__init__(self,tabuStr)
        self.setParameter('statewise',1)

    def setParameter(self,name,value):
        if name == "apps":
            self.log("APPS")
            appNames = value.split()
            self._tabuFilter = createAppNameFilter(appNames)
            # _actFilter deals with "X ACTIVATES Y" kinda switches
            self._actFilter = createActivatesFilter(appNames)
        elif name == "statewise":
            try: self._statewise = not not int(value)
            except ValueError:
                raise ValueError("statewise must be either 0 or 1")
            if self._statewise:
                self.filterRelevant = self._filterRelevantStatewise
            else:
                self.filterRelevant = self._filterRelevantAppwise
        else:
            SingleTabuRequirement.setParameter(self,name,value)

    def markExecuted(self, transition):
        TabuRequirement.markExecuted(self,transition)
        for fromApp in self._tabuFilter(transition):
            self._fromApp = fromApp
            self._fromState = transition.getDestState()
            break
        for fromApp,toApp in self._actFilter(transition):
            self._fromApp = toApp

    def _filterRelevantStatewise(self,transition):
        for toApp in self._tabuFilter(transition):
            if self._fromApp is not None and self._fromApp != toApp:
                yield (self._fromState,transition.getDestState())

        for fromApp,toApp in self._actFilter(transition):
            yield (transition.getSourceState(), transition.getDestState())

    def _filterRelevantAppwise(self,transition):
        for toApp in self._tabuFilter(transition):
            if self._fromApp is not None and self._fromApp != toApp:
                yield (self._fromApp, toApp)

        for fromApp,toApp in self._actFilter(transition):
            yield (fromApp, toApp)

    def push(self):
        self._fromStack.append( (self._fromApp,self._fromState) )
        TabuRequirement.push(self)

    def pop(self):
        self._fromApp,self._fromState = self._fromStack.pop()
        TabuRequirement.pop(self)


def _parseSize(size):
    if size in ("","infinity","infinite","inf","unlimited"):
        retSize = None
    else:
        try:
            retSize = int(size) # may raise ValueError
            if retSize < 0: raise ValueError()
        except ValueError:
            raise ValueError("Invalid size: '%s'. "%size + 
                "It should be a natural number or 'infinite'.")
    return retSize


# "tabu filters" take a transition as a parameter.
# if the transition is something the tabu filter is intrested in, it yields
# something that identifies the thing they're tabuing.
# Eg. destStateFilter yields the destination state of the transition.
# yielding instead of returning because there may be multiple things to yield,
# like in statePropFilter.

def destStateFilter(transition):
    yield str(transition.getDestState())

def sourceStateFilter(transition):
    yield str(transition.getSourceState())

def transitionFilter(transition):
    yield transition

def edgeFilter(transition):
    yield transition.getAction()

def startAWFilter(transition):
    action = transition.getAction()
    if "start_aw" in str(action) and "TaskSwitcherGEN" not in str(action):
        yield action

def sourceStateOfStartAWFilter(transition):
    for a in startAWFilter(transition):
        yield transition.getSourceState()

def destStateOfStartAWFilter(transition):
    for a in startAWFilter(transition):
        yield transition.getSourceState()

def endAWFilter(transition):
    action = transition.getAction()
    if "end_aw" in str(action) and "TaskSwitcherGEN" not in str(action):
        yield action

def sourceStateOfEndAWFilter(transition):
    for a in endAWFilter(transition):
        yield transition.getSourceState()

def destStateOfEndAWFilter(transition):
    for a in endAWFilter(transition):
        yield transition.getDestState()

def wakeFilter(transition):
    if str(transition.getAction()).startswith("WAKEtsWAKE"):
        yield True

def keywordFilter(transition):
    action = transition.getAction()
    if str(action).startswith("kw"): # or "kw_"?
        yield action

def statePropFilter(transition):
    action = transition.getAction()
    # getStateProps() sometimes seems to return multiple equal stateProps.
    # yielding only one of each.
    props = set()
    for sp in transition.getSourceState().getStateProps():
        if "SleepState" not in str(sp):
            props.add( str(sp) )
    for spStr in props:
        yield spStr

def statePropInclSleepFilter(transition):
    action = transition.getAction()
    # getStateProps() sometimes seems to return multiple equal stateProps.
    # yielding only one of each.
    props = set()
    for sp in transition.getSourceState().getStateProps():
        props.add( str(sp) )
    for spStr in props:
        yield spStr

def createAppNameFilter(appNames):
    def appNameFilter(transition):
        aStr = str(transition.getAction())
        for app in appNames:
            if aStr.startswith(app):
                yield app
    return appNameFilter

_RE_ACTIVATES = re.compile("(.*) ACTIVATES (.*)")
def createActivatesFilter(appNames):
    def appNameFilter(transition):
        aStr = str(transition.getAction())
        if not " ACTIVATES " in aStr:
            return
        x, y = _RE_ACTIVATES.match(aStr).groups()
        if "/" in x:
            # if there's a device name in x, prepend it y also
            y = x.split("/",1)[0] + "/" + y
        a1, a2 = None, None
        for app in appNames:
            if x.startswith(app):
                a1 = app
            if y.startswith(app):
                a2 = app
        if a1 and a2 and (a1 != a2):
            yield (a1,a2)
    return appNameFilter

def createWakeFilter(appNames):
    _wake_re = re.compile(
        r"WAKEtsWAKE<(%s).*>" % 
        (r"|".join(["(?:%s)" % a for a in appNames])) )
    def wakeFilter(transition):
        for app in _wake_re.findall( str(transition.getAction()) ):
            yield app
    return wakeFilter

def createSleepFilter(appNames):
    _sleep_re = re.compile(
        r"SLEEPts<(%s).*>" % 
        (r"|".join([r"(?:%s)" % a for a in appNames])) )
    def sleepFilter(transition):
        for app in _sleep_re.findall( str(transition.getAction()) ):
            yield app
    return sleepFilter

def createOfFilter(thisOf,ofThis):
    def ofFilter(transition):
        for unused in ofThis(transition):
            break
        else:
            return
        for item in thisOf(transition):
            yield item
    return ofFilter


def createCompoFilter(filters):
    """ Takes some filters and returns a filter that yields all the possible
        tuples of the form (y1,y2,...) where y1 is something yielded by
        the first filter, and so on.

        Eg. createCompoFilter( [startAWFilter,statePropFilter] )
        returns a filter that yields all the (action,stateprop) pairs of
        the given transition.
    """
    def compoFilter(transition):
        startsOfTuples = [ () ]
        for filt in filters:
            oneLongerStartsOfTuples = []
            for sot in startsOfTuples:
                for x in filt(transition):
                    oneLongerStartsOfTuples.append( sot+(x,) )
            startsOfTuples = oneLongerStartsOfTuples
        # they're full tuples now
        for t in startsOfTuples:
            yield t
    return compoFilter


def createComponentTransitionFilter(comps=None):
    if comps is None:
        # all the components
        def componentTransitionFilter(transition):
            numComps = len(transition.getSourceState()._id)
            for n in xrange(numComps):
                # does the state of component n change?
                source = transition.getSourceState()._id[n]._id
                dest = transition.getDestState()._id[n]._id
                if source != dest:
                    yield (n,source,str(transition.getAction()),dest)
        componentTransitionFilter.__doc__ = """
            Yields all the component transitions that are executed when
            the given (parallel) transition is executed."""
    else:
        # only the given component indices
        def componentTransitionFilter(transition):
            for n in comps:
                # does the state of component n change?
                source = transition.getSourceState()._id[n]._id
                dest = transition.getDestState()._id[n]._id
                if source != dest:
                    yield (n,source,str(transition.getAction()),dest)
        componentTransitionFilter.__doc__ = """
            Yields all the transitions of components %s that are executed when
            the given (parallel) transition is executed.""" % (comps,)
    return componentTransitionFilter

def createUndefinedFilter(text):
    def filter(*args):
        raise ValueError(text)
    return filter


TABU_FILTERS = {
    "sourcestate": sourceStateFilter,
    "deststate": destStateFilter,
    "state": destStateFilter,
    "transition": transitionFilter,
    "edge": edgeFilter,
    "keyword": keywordFilter,
    "kw": keywordFilter,
    "stateprop": statePropFilter,
    "stateproposition": statePropFilter,
    "statepropinclsleep": statePropInclSleepFilter,
    "wake": wakeFilter,
    "end_aw": endAWFilter,
    "start_aw": startAWFilter,
    "aw": startAWFilter,
    #"action": startAWFilter, # 'action' is too ambiguous...
    "source_state_of_start_aw": createOfFilter(sourceStateFilter,startAWFilter),
    "source_state_of_end_aw": createOfFilter(sourceStateFilter,endAWFilter),
    "dest_state_of_start_aw": createOfFilter(destStateFilter,startAWFilter),
    "dest_state_of_end_aw": createOfFilter(destStateFilter,endAWFilter),
    "stateprop_of_endaw": createOfFilter(statePropFilter, endAWFilter),
    "componenttransition": createComponentTransitionFilter(),
    "switch": createUndefinedFilter("switch needs a param 'apps'")
}

def tabuFilterByType(filterName):
    if filterName in TABU_FILTERS:
        return TABU_FILTERS[filterName]
    raise ValueError("Invalid filter name: '%s'"%(filterName,)) 

