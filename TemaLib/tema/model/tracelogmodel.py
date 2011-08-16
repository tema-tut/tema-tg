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
TracelogModel takes the test log of a previous test execution. The log
is used as a model that consists of a linear sequence of keywords sent
by the adapter.
"""

import tema.model.model as model
import re

_sent_keyword_line=re.compile("^([0-9]+\.[0-9]+) Adapter: Sending \[(.*)\]$")
_execution_status_line=re.compile("^([0-9]+\.[0-9]+) Adapter: The client reported (successful|unsuccessful) execution of \[(.*)\]$")

Action=model.Action

State=model.State

Transition=model.Transition

class TracelogModel(model.Model):
    def __init__(self):
        model.Model.__init__(self)
        self._file_line_number=0
        self._actions=[]
        self._action_hash={}
        self._initial_state=None

    def log(self,msg): pass

    def _find_line_matching(self,fileobj,regexp):
        # returns current line number with None (end of file reached
        # without finding a line matching regexp) or a tuple of group
        # contents of regexps
        l=fileobj.readline()
        self._file_line_number+=1
        while l:
            matches=regexp.findall(l)
            if matches and len(matches[0][0])>1:
                return self._file_line_number, matches[0]
            l=fileobj.readline()
            self._file_line_number+=1
        return self._file_line_number,None

    def loadFromFile(self,fileobj):
        self._initial_state=model.State(0,[])
        last_state=self._initial_state
        states=1
        while True:
            # 1. Read sent keyword
            lineno,sent_tuple=self._find_line_matching(fileobj,_sent_keyword_line)
            if not sent_tuple: break # end-of-file, good.

            # 2. Find its execution status
            lineno,report_tuple=self._find_line_matching(fileobj,_execution_status_line)
            if not report_tuple:
                self.log("Execution status missing for keyword sent at line" +
                         " %s ('%s [%s]')" % (lineno, sent_tuple[0],sent_tuple[1]))
                raise Exception("Unexpected end of file")
            elif sent_tuple[1]!=report_tuple[2]:
                self.log("Execution status missing for keyword sent at line"+
                         " %s ('%s [%s]')" % (lineno, sent_tuple[0],sent_tuple[1]))
                self.log("Found execution status for keyword"+
                         " '%s' instead (at line %s)" % (report_tuple[2],lineno))
                raise Exception("Mismatching execution status")
            
            # 3. Add this action to the sequence
            if report_tuple[1]=='successful': new_action_name=sent_tuple[1]
            else: new_action_name=Action(None,sent_tuple[1]).negate()
                
            if not new_action_name in self._action_hash:
                new_action=Action(len(self._actions),new_action_name)
                self._action_hash[new_action_name]=new_action
                self._actions.append(new_action)
                
            new_action=self._action_hash[new_action_name]                 
            new_state=model.State(states,[])
            states+=1
            new_transition=model.Transition(last_state,new_action,new_state)
            
            last_state._outTransitions=[new_transition]
            last_state=new_state
        # File has been read now.
        self.log("Trace read. Keywords: %s, States: %s" % (len(self._actions),states))
        new_action=Action(len(self._actions),"-- All keywords executed.")
        self._actions.append(new_action)
        self._action_hash[new_action.toString()]=new_action
        new_state=model.State(states,[])
        new_transition=model.Transition(last_state,new_action,new_state)
        last_state._outTransitions=[new_transition]

    def getInitialState(self):
        return self._initial_state

    def getActions(self):
        return self._actions

Model=TracelogModel
