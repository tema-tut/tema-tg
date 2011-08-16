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

class InitEngineError(Exception): pass

import random

class InitEngine:
    """
    This class reads --initmodel arguments and executes the given test
    models until it reaches a deadlock.
    """
    def log(self,*a): pass

    def __init__(self):
        self.log("Initializing")
        self._modelnames=[]
        self._models=[]
        try: self._guidance=__import__("tema.guidance.randomguidance",globals(),locals(),['']).Guidance()
        except Exception, e:
            self.log("Failed to load randomguidance.")
            raise Exception("Error '%s' when loading tema.guidance.randomguidance." % e)
        
    
    def setParameter(self,name,value):
        """
        name defines the model interface (lstsmodel,
        parallellstsmodel, ...).
        value is the name of the file from which the model can be
        loaded.
        """
        self.log("Loading file '%s' through interface '%s'" % (value,name))
        try: model = __import__("tema.model."+name,{},{},['']).Model()
        except Exception, e:
            raise Exception("Error '%s' when loading interface '%s'." % (e,name))
        model.loadFromFile(file(value))
        self._modelnames.append(value)
        self._models.append(model)
    
    def _run_model(self, testmodel, testdata, adapter, appchain):
        stepcounter=0
        current_state=testmodel.getInitialState()
        guidance=self._guidance

        while len(current_state.getOutTransitions())>0:
            stepcounter+=1
            # 1. Choose action to be executed
            suggested_action=guidance.suggestAction(current_state)
            # 2. Send it to the adapter
            if suggested_action.isNegative():
                action_name=suggested_action.negate()
            else:
                action_name=suggested_action.toString()
            try:
                result = adapter.sendInput(
                    appchain.process(
                    testdata.processAction(
                    action_name)))
            except Exception, e:
                self.log("Sending input caused error: '%s'" % e)
                raise e
            if (result==True and not suggested_action.isNegative()) or \
                   (result==False and suggested_action.isNegative()): # executed successfully
                executed_action_name=action_name
            elif (result==True and suggested_action.isNegative()) or \
                     (result==False and not suggested_action.isNegative()):
                executed_action_name=suggested_action.negate()

            # 3. Find out which transition in the model matches to
            # executed_action_name

            possible_transitions=[ t for t in current_state.getOutTransitions() \
                                   if t.getAction().toString()==executed_action_name ]
            
            if possible_transitions==[]:
                self.log("Cannot execute action '%s' in state '%s'"
                         %(executed_action_name,current_state))
                raise InitEngineError("Cannot execute action '%s' in state '%s'"
                                      % (executed_action_name,current_state))

            # 4. Execute the transition (if many, print warning on nondeterminism)
            chosen_transition=random.choice(possible_transitions) 
            if len(possible_transitions)>1:
                print "Non determinism:",[str(t) for t in possible_transitions]

            self.log("Executing: %s" % chosen_transition.getAction())
            self.log("New state: %s" % chosen_transition.getDestState())

            # --- markExecuted is not called here

            current_state=chosen_transition.getDestState()
        # end while loop
        self.log("Deadlock reached.")

    def run_init(self, adapter, testdata, appchain):
        self.log("Starting initialization, going through %s model(s)."
                 % len(self._models))
        for mindex, m in enumerate(self._models):
            self.log("Initialization run %s/%s ('%s')"
                     % (mindex+1,len(self._models),self._modelnames[mindex]))
            self._run_model(m,testdata,adapter,appchain)
        self.log("Initialization done.")
