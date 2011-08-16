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

Action=model.Action

Transition=model.Transition

StateProp=model.StateProp

# State proposition semantics could be any of these:

sps_DUMMY, sps_STICKY = range(2)

class State(model.State):
    """
    ParallelModel state is a tuple of states of component models.
    """
    def __init__(self,globalStateId,outTransitions,parallelmodel=None):
        model.State.__init__(self,globalStateId,outTransitions)
        self._model=parallelmodel
        self._str_representation=str(tuple([ int(str(s)) for s in self._id ]))
    def __str__(self):
        return self._str_representation

    def getOutTransitions(self):
        """Returns list of transitions that leaves the state."""
        if self._outTransitions==None:
            # If the out transitions were not already given, ask the
            # model to calculate them for us
            self._outTransitions=self._model._getOutTransitions(self._id)
        return self._outTransitions

    def getStateProps(self):
        return self._model._getStateProps(self._id)

    def clearCache(self):
        self._outTransitions=None

    def equals(self,state):
        return str(self)==str(state)

    def __eq__(self,state):
        return self.equals(state)

    def __hash__(self):
        return hash(tuple(self._id))


class ParallelModel(model.Model):
    """
    Generic parallel composer. Components that implement model
    interface are composed in parallel.

    To use methods implemented here, inherited object should set

    self._modellist     - a list of Model objects
    self._rulelist      - should be a RuleList object
    self._actionmapper  - for int2act and act2int conversions
    """
    def __init__(self):
        self._modellist=None
        self._rulelist=None
        self._stateCache={}
        self._actionCache={}
        self._statepropCache={}
        self._stateprop_semantics = sps_STICKY

    def getInitialState(self):
        return State([m.getInitialState() for m in self._modellist],None,self)

    def clearCache(self):
        for s in self._stateCache.itervalues():
            s.clearCache()
        self._stateCache={}

    def _newState(self,stateid):
        if str(stateid) in self._stateCache:
            return self._stateCache[str(stateid)]
        else:
            s = State(stateid,None,self)
            self._stateCache[str(stateid)] = s
            return s

    def _newStateProp(self, submodel_number, submodel_statepropobj):
        # stateprop_id is a pair (modelnumber, stateprop)
        stateprop_id = (submodel_number, submodel_statepropobj)
        if stateprop_id in self._statepropCache:
            return self._statepropCache[stateprop_id]
        else:
            sp = StateProp(stateprop_id,
                           "%s.%s" % (submodel_number, submodel_statepropobj))
            self._statepropCache[stateprop_id] = sp
            return sp

    def _newAction(self,actionid):
        if actionid in self._actionCache:
            return self._actionCache[actionid]
        else:
            a = Action(actionid,self._actionmapper.int2act(actionid))
            self._actionCache[actionid] = a
            return a

    def getStatePropList(self):
        rv = []
        for modelnum, m in enumerate(self._modellist):
            for sp in m.getStatePropList():
               rv.append(self._newStateProp(modelnum, sp))
        return rv

    def _getStateProps(self,state_id):
        if self._stateprop_semantics == sps_STICKY:
            # in STICKY state proposition semantics, the set of state
            # propositions in a compound state is the union of sets of
            # state propositions of the substates.
            rv = []
            for modelnum, state in enumerate(state_id):
                for local_sp in state.getStateProps():
                    global_sp = self._newStateProp(modelnum, local_sp)
                    rv.append(global_sp)
            return rv
        elif self._stateprop_semantics == sps_DUMMY:
            return []
        else:
            raise Exception("Unsupported state proposition semantics: %s"
                            % (self._stateprop_semantics,))

    def _getOutTransitions(self,state_id):
        """This method is called from a state object."""
        rv=[]

        # 1. Find out the enabled transitions in all component states
        avail_transitions=[]
        for s in state_id: # state_id is a tuple of states
            avail_transitions.extend([t for t in s.getOutTransitions()])
            
        # 2. Find out which rules are enabled when these actions can
        # be executed
        #enabled_rules=self._rulelist.enabled(
        #    [ t.getAction()._id for t in avail_transitions ])
        enabled_rules=self._rulelist.enabled(
            set([ t.getAction()._id for t in avail_transitions ]))
        
        # 3. Find transitions corresponding to the enabled rules
        source_state=self._newState(state_id)
        for rule in enabled_rules:
            # dest_states = list of state tuples
            dest_states=[()]
            syncacts=rule.getSynchronousActions()
            for state in state_id:
                ds=[]
                for t in state.getOutTransitions():
                    if t.getAction()._id in syncacts:
                        ds.append(t.getDestState())
                if ds==[]: ds.append(state)
                for new_ds in ds:
                    dest_states=[ odtuple+(new_ds,) for odtuple in dest_states ]
            # generate new transitions based on dest_states
            for ds in dest_states:
                rv.append(
                    Transition( source_state,
                                self._newAction( rule.getResult() ),
                                self._newState(ds) )
                    )
        return rv

Model=ParallelModel
