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

""" StateVerifier returns an action that executes state verification (sv).

Stateverifier is kind of like a Guidance, except:
    - it only has two methods: getAction and markExecuted
      (no setTestModel, addRequirement, etc.)
    - if there are no state verifications to execute,
      getAction() returns None.
      (In that case some other Guidance must decide what action to execute.)
"""

def _is_start_sv(action):
    return 'start_sv' in str(action)
def _is_end_sv(action):
    return 'end_sv' in str(action)

class StateVerifier:
    def __init__(self):
        self._currSv = None # the sv we're currently verifying
        self._svsChecked = set() # the svs we've already checked in this state

    def getAction(self,current_state):
        """ Returns an action that executes a state verification.
            This only executes an sv once during one visit to a state.
            If no new sv can be executed from the given state, returns None
                -> some (other) guidance should choose the action.
        """
        acts = [t.getAction() for t in current_state.getOutTransitions()]
        if self._currSv is not None:
            # on a verification loop
            if len(acts) != 1:
                # TBD: dunno if verification loop could branch out...
                # in such case, let some other guidance decide what to do
                return None
            return acts[0]
        else:
            # not on a verification loop, see if there are sv's to check
            svs = [a for a in acts if _is_start_sv(a) and
                                      a not in self._svsChecked]
            return svs[0] if svs else None

    def markExecuted(self,transition):
        """ Must be called after every transition execution."""
        if _is_start_sv(transition.getAction()):
            # verification loop started
            self._currSv = transition.getAction()
        elif _is_end_sv(transition.getAction()):
            # verification loop ended
            self._svsChecked.add(self._currSv)
            self._currSv = None
        elif self._currSv is None:
            # executed a transition outside a verification loop
            self._svsChecked.clear()
