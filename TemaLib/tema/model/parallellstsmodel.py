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

# sys.path should be such that rules, rules_parser, lsts and lstslist
# can be imported

import tema.rules.rules as rules
import tema.rules.rules_parser as rules_parser

import tema.lsts.lsts as lsts
import tema.lsts.lstslist as lstslist

import tema.model.model as model
import tema.model.lstsmodel as lstsmodel

import os # os.sep needed in path name strings

from tema.model.parallelmodel import ParallelModel,Action,Transition,State

class ParallelLstsModel(ParallelModel):
    def __init__(self):
        ParallelModel.__init__(self)
        self._lstslist=lstslist.LstsList()
        self._rulelist=rules.RuleList()
        self._dirprefix=""

    def log(self,*args):
        pass # this should be replaced by a true logger

    def getActions(self):
        return [self._newAction(i)
                for i in range(self._first_result_action_index,
                               self._last_result_action_index+1)]
        
    def loadFromObject(self,rules_file_contents=None):
        parser=rules_parser.ExtRulesParser()
        
        # Load LSTSs mentioned in the rules to the lstslist
        lstss=parser.parseLstsFiles(rules_file_contents)
        for lstsnum,lstsfile in lstss:
            lstsobj=lsts.reader()
            if self._dirprefix:
                filename=self._dirprefix+"/"+lstsfile
            else:
                filename=lstsfile
            try:
                lstsobj.read(file(filename))
                self.log("Model component %s loaded from '%s'" % (len(self._lstslist),filename))
            except Exception,(errno,errstr):
                raise ValueError("Could not read lsts '%s':\n(%s) %s" % (filename,errno,errstr))
            self._lstslist.append((lstsnum,lstsobj))

        # Create global action numbering
        self._lstslist.createActionIndex()

        self._first_result_action_index=self._lstslist.getActionCount()

        # Convert rules into global action numbers
        # and append to rulelist
        for rule in parser.parseRules(rules_file_contents):
            syncact=[]
            result=""
            # go through syncronized actions (everything except the last field)
            try:

                for lstsnum,actname in rule[:-1]:
                    syncact.append( self._lstslist.act2int("%s.%s" % (lstsnum,actname)) )
                    
                result=rule[-1]
            
                self._lstslist.addActionToIndex(result)
                self._rulelist.append(rules.Rule(syncact,self._lstslist.act2int(result)))
            except: # ??? catch the right exception only!!! (thrown by act2int)
                # the rule may have referred to non-existing actions
                pass

        self._last_result_action_index=self._lstslist.getActionCount()-1

        # LSTSs are handled through model interface, so store them to
        # modellist.
        self._modellist=[ lstsmodel.LstsModel(litem[1]) for litem in self._lstslist ]
        for m in self._modellist: m.useActionMapper(self._lstslist)
        self._actionmapper=self._lstslist

    def loadFromFile(self,rules_file_object):
        # Try to find out a directory for lsts files
        if not self._dirprefix and os.sep in rules_file_object.name:
            try: self._dirprefix=rules_file_object.name.rsplit(os.sep,1)[0]
            except: pass
        return self.loadFromObject(rules_file_object.read())

    def setLSTSDirectory(self,dirname):
        """Every LSTS mentioned in the rules file will be prefixed with dirname/"""
        self._dirprefix=dirname

Model=ParallelLstsModel
