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

class Actionmapper:
    def __init__(self):
        self.__act2int={}
        self.__int2act=[]
        
    def addActionToIndex(self,actionname):
        self.__int2act.append(actionname)
        self.__act2int[actionname]=len(self.__int2act)-1

    def getActionCount(self):
        return len(self.__int2act)

    def act2int(self,act_name):
        return self.__act2int[act_name]

    def int2act(self,act_index):
        return self.__int2act[act_index]


class LstsList(list,Actionmapper):
    """LstsList contains pairs (lsts number (integer), lsts (lsts
    instance))"""
    def __init__(self,*args):
        list.__init__(self,*args)
        Actionmapper.__init__(self)
    def createActionIndex(self):
        """Call this method only once! It will build a global action
        dictionary and change the action numbers in the transitions of
        the LSTSs to correspond to the number in the global index."""
        for lsts_number,lsts in list.__iter__(self):
            for act in lsts.get_actionnames():
                global_actname="%s.%s" % (lsts_number,act)
                self.addActionToIndex(global_actname)

            a=lsts.get_actionnames()
            new_transitions=[]
            for i,tranlist in enumerate(lsts.get_transitions()):
                new_tranlist=[]
                for dest_state,act_num in tranlist:
                    global_actname="%s.%s" % (lsts_number,a[act_num])
                    new_tranlist.append( (dest_state,self.act2int(global_actname)) )
                new_transitions.append(new_tranlist)
            lsts.set_transitions(new_transitions)
        
