#!/usr/bin/env python
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
GT is a tool for making graph transformations on LSTSes.

Usage: gt [options] input_lsts output_lsts "rule" [ "rule" ... ]

Options are:

    -h, --help     print this information

    --debug
    -v, --verbose  print detailed information in rule duplication

    --version      print version number of this tool

    --keep-labels  do not throw away unreachable actions or state propositions

Rule syntax in BNF, (x* is zero or more x, x+ is one or more x,
[x] is optional x, x|y is either x or y)

rule             ::= [apply-spec] (rule-element)* -> (rule-element)*
apply-spec       ::= 'once:' | 'repeat until no match:'
rule-element     ::= transition-match | stateprop-match | requirement
                     | output | quantification | 'BREAK'
transition-match ::= '[!]T(' field ',' field ',' field ')'
stateprop-match  ::= '[!]P(' field ',' field ')'
requirement      ::= 'REQ[' boolean-expression-in-python ']'
output           ::= 'OUT[' ( text | replexp | variable-name )* ']'
quantification   ::= 'Q[' variable-name 'in' ('A'|'P'|'S') ']'
field            ::= variable-name | content-match
variable-name    ::= ( letters | digits | '_' | ''' )+
content-match    ::= '"' ( text | regexp | replexp )* '"'
regexp           ::= '${' anything-but-} '}'
replexp          ::= '$=' digits '.'

input_lsts is a file name, "-" for standard input, or "new" to
start with a single state lsts. output_lsts is a file name, "-"
for standard output or "none" if the resulting lsts should not be
printed out.

Rules are divided in the left hand side (LHS) and the right hand side
(RHS). The basic idea is that LHS of a rule specifies a pattern in the
input lsts, if the rule is the first one, or in the lsts resulting
from the application of the previous rule. If the pattern is found, it
is removed and what is on RHS is added to the lsts. When all rules
have been applied, the resulting lsts can then be written out.

Rules consist of rule elements, like a transition match pattern, which
again consist of fields, for instance the source state of a transition
match. The value of a field can be either a string, which may contain
regular expressions, or the name of a variable. The first occurence of
a variable is called free variable.

A rule is abstract as long as there are variables or regular
expressions in its fields. Rules must be made concrete before they can
be applied. This happens field by field starting from the left most
field of the rule. On every step, the rule is made less abstact by
giving a concrete value to the variable and the regular expressions in
the field. If there are more than one matching concrete value, the
whole rule (in case of a positive match) or the element inside the
rule (in case of a negative match) is copied so that every matching
value appears in the field of one copy.

Rule elements can be any of the following:

1. T(source_state,action,dest_state) or P(state,proposition). These
   elements are positive matches to transitions and propositions. When
   appearing on LHS (RHS), matching transitions and propositions will
   be removed (added).

   On LHS, free variables are allowed in any fields of the elements.
   Variables will be given all matching values and the rest of the
   occurences of the variables are bound. See example 1.

   On RHS, free variables are allowed only in the state fields of
   elements. They are associated with a single new value and their
   values are bound in the later occurences. See example 3.

2. !T(source_state,action,dest_state) or !P(state,proposition). These
   are negative matches to transitions and propositions. If a rule
   contains one matching negative element, the whole rule is
   dropped. Free variables appearing in the fields of these elements
   are not bound (they get all possible values in the same rule). See
   example 7.

3. REQ[ boolean expression in python ] is a special rule element for
   stating extra requirements in the rule. When this element is made
   concrete, the expression in brackets is evaluated in Python with
   eval function. If it returns True, the element is silently removed
   from the rule. If it returns False, the whole rule is
   dropped. Otherwise, execution of the program is stopped with an
   error. Note that every string that look like a variable name will
   be replaced by the value of the variable in the expression. See
   example 8.

4. OUT[ string ] is a special rule element for outputting text during
   the transformation. It is useful for inspecting some properties of
   input LSTSes and debugging the rules. When this element is made
   concrete the string is written to standard error and the element is
   removed from the rule.

5. Q[ q in set ] gives variable q every value in the set. Predefined
   sets are consist of names of actions (A), names of propositions (P)
   and names of states (S).

6. BREAK is a special rule for stopping the execution. If this element
   is made concrete, program quits immediately.

Examples of rules:

1. Change transitions whose labels start with letter "a" to "tau":
   'T(s0,"${a.*}",s1) -> T(s0,"tau",s1)'

2. Add prefix "pre" to actions starting with "a":
   'T(s0,"${a.*}",s1) -> T(s0,"pre$=1.",s1)'

3. Duplicate transitions labelled "b" by introducing a new state
   in-between:
   'T(s0,"b",s1) -> T(s0,"b",s_new) T(s_new,"b",s1)'

4. Join "a" and "b" transitions into one "ab" transition:
   'T(s0,"a",s1) T(s1,"b",s2) -> T(s0,"ab",s2)'

5. Delete state proposition "c" and add a loop to the same state with
   a transition labelled "d":
   'P(s0,"c") -> T(s0,"d",s0)'

6. Delete "tau" loops in all states and add "divergence" proposition
   to the same states:
   'T(s0,"tau",s0) -> P(s0,"divergence")'

7. Add proposition"deadlock" to every state that is a destination state
   of some transition but not a source state of any transitions.
   'T(s0,a,s1) !T(s1,b,s2) -> T(s0,a,s1) P(s1,"deadlock")'

8. Change every transition starting from destination states of tau
   transitions to start from the source states of the tau transitions
   and remove the tau transitions. It is required with REQ that the
   starting and the ending states of the tau transitions should
   differ:
   'T(s0,"tau",s1) REQ[s0!=s1] T(s1,a,s2) -> T(s0,a,s2)'

9. Add transitions to "failure" state with every action that cannot be
   executed in the source state.
   'Q[s in S] Q[a in A] !T(s,a,any) -> T(s,a,"failure")'

Examples of commands:

1. Create a one-state LSTS and print it to standard output

   gt new -

2. Create an LSTS with a tau loop and "a" transition to a deadlock
   state with a "deadlock" propositon on. Note that there is special
   state proposition "gt:istate" in the initial state of the input lsts.
   The proposition is not printed out to the resulting lsts.

   gt new - 'P(s,"gt:istate")->T(s,"tau",s)T(s,"a",s1)P(s1,"deadlock")'

3. Store the reachable part of i.lsts to o.lsts. Actions and state
   propositions that not used in the reachable part will be removed.

   gt i.lsts o.lsts

4. Print out the state propositions in i.lsts

   gt i.lsts none 'Q[p in P] OUT[p]->' 2>&1 | sort -u

5. Print a shortest path from the initial state to a state with "coffee"
   state proposition:

   gt i.lsts none 'P(si,"gt:istate") -> P(si,"cs")' \\
                  'repeat until no match:
                       P(s0,"${cs.*}") !P(s0,"coffee")
                       T(s0,"${.*}",s1)
                       ->
                       P(s1,"$=1.=>$=2.")' \\
                  'P(s,"coffee") P(s,"cs=>${.*}")
                   OUT[Found coffee: $=1.] BREAK ->' \\
                   'OUT[Could not find coffee.] ->'

Author: (2006) Antti Kervinen, teams@cs.tut.fi
"""

# TODO:
# negative rule expansion should not expand to many absrules but
# many negative rules to the same absrule!

version="0.10"
debugflag=0

import sys
import re
import copy
import os

import tema.lsts.lsts as lsts


# Rule syntax:
reflags=re.DOTALL|re.MULTILINE
tr_re=re.compile("([!]?)T\(\s*([^),]+)\s*,\s*([^),]+)\s*,\s*([^),]+)\s*\)",reflags)
sp_re=re.compile("([!]?)P\(\s*([^),]+)\s*,\s*([^),]+)\s*\)",reflags)
req_re=re.compile("REQ\[([^]]+)\]",reflags)
print_re=re.compile("OUT\[([^]]+)\]",reflags)
quant_re=re.compile("Q\[([a-zA-Z0-9_']+)\s+in\s+([^]]+)\]",reflags)
break_re=re.compile("BREAK")
apply_spec_re=re.compile("(once:|repeat until no match:)")
separator=re.compile("(.*)->(.*)",reflags)
re_variable_name=re.compile("[a-zA-Z0-9_']+")
re_regexps=re.compile('\$\{([^}]+)\}')

class GTError(Exception):
    """ For errors in graph transformation """
    pass

def error(s,exitval=1):
    print >>sys.stderr,"gt: %s" % s
    sys.exit(exitval)

def debugmsg(s,msg_level=1):
    if msg_level<=debugflag:
        print >>sys.stderr,"gt: %s" % s

def convert_to_regexp(s):
    """
    Eats expression with ${}-items and converts it to a "regular"
    regular expression.
    """
    orig_str=s
    m=re_regexps.search(s)
    result=""
    while m:
        result+=re.escape(s[:m.start(1)-2]) # non-regexp part
        result+="(%s)" % m.group(1) # regexp part
        s=s[m.end(1)+1:] # the rest in next loop
        m=re_regexps.search(s)
    result+=re.escape(s) # the rest does not contain regexp -> escape
    try:
        result_re=re.compile(result)
        # debugmsg("regexp: %s" % result)
        return result_re
    except Exception,e:
        raise GTError("Not a valid regular expression: '%s'" % orig_str)
#        error("Not a valid regular expression: '%s'" % orig_str)
    

class Transition(object):
    def __init__(self,source,action,dest):
        self.source=str(source)
        self.action=str(action)
        self.dest=str(dest)
    def __str__(self):
        return "Transition(%s,%s,%s)" % (self.source,self.action,self.dest)

class Proposition(object):
    def __init__(self,state,proposition_name):
        self.state=str(state)
        self.prop=str(proposition_name)

class LstsData(object):
    """
    This class will be used for storing transition and state
    proposition information of a lsts and providing short-cuts for
    accessing the information by source states, actions, destination
    states and (proposition) states.
    """
    __slots__=['tr','pr','ac','pr_hash','tr_by_ss','pr_by_st','initial_state']

    def __str__(self):
        return "LstsData(#tr=%s,#pr=%s)" % (len(self.tr),len(self.pr))

class RuleElementList(list):
    def __str__(self):
        return "[%s]" % ",".join([str(i) for i in self])

class Rule(object):
    """
    Abstract graph transformation rule
    """
    def __init__(self):
        self.lhs=RuleElementList()
        self.rhs=RuleElementList()
        self.next_regex=1
        self.apply_spec='once:'

    def __str__(self):
        return "Rule: %s -> %s" % (self.lhs,self.rhs)

class TRRule(object):
    """
    Transition rule element
    """
    string_slots=['source','action','dest','neg']
    def __init__(self,sourcestr,actionstr,deststr,negstr):
        self.source=sourcestr
        self.action=actionstr
        self.dest=deststr
        self.neg=negstr
        self.is_abstract=1

    def __str__(self):
        return "%sT(%s,%s,%s)" % (self.neg,self.source,self.action,self.dest)

class PRRule(object):
    """
    State proposition rule element
    """
    string_slots=['state','prop']
    def __init__(self,statestr,propstr,negstr):
        self.state=statestr
        self.prop=propstr
        self.neg=negstr
        self.is_abstract=1

    def __str__(self):
        return "%sP(%s,%s)" % (self.neg,self.state,self.prop)

class ReqRule(object):
    """
    Evaluates boolean expression.
    """
    string_slots=['expression']
    def __init__(self,expression):
        self.expression=expression
        self.is_abstract=0
    def __str__(self):
        return "REQ[%s]" % self.expression
    def evaluate(self):
        try: 
            t=eval(self.expression)
        except Exception,e: 
            raise GTError("Cannot evaluate: '%s'" % self.expression)
#            error("Cannot evaluate: '%s'" % self.expression)
        if not t in [True,False]:
#            error("Expression '%s' did not return boolean value." % self.expression)
            raise GTError("Expression '%s' did not return boolean value." % self.expression)
        return t

class QRule(object):
    """
    Contains quantification of a variable over a set
    """
    string_slots=['variable','setdef']
    def __init__(self,varname,setdef):
        self.variable=varname
        self.setdef=setdef
        self.is_abstract=1
    def __str__(self):
        return 'Q[%s in %s]' % (self.variable,self.setdef)
    
    

class PrintRule(object):
    """
    Rule element for printing out messages
    """
    string_slots=['message']
    def __init__(self,message):
        self.message=message
        self.is_abstract=0
        
    def __str__(self):
        return "OUT[%s]" % self.message

    def output(self):
        print >>sys.stderr,self.message

class BreakRule(object):
    """
    Rule element for stopping the execution.
    """
    string_slots=[]
    def __init__(self):
        self.is_abstract=0

    def __str__(self):
        return "BREAK"
    

def parse_rulestr(s):

    def parse_string(s,result_rules):
        """
        Appends rules found in s to result_rules list.
        Returns 0 if succeeded, otherwise n which is the
        length of unparsed portion of s.
        """
        s=s.lstrip()
        while s:
            trm=tr_re.match(s)
            spm=sp_re.match(s)
            reqm=req_re.match(s)
            quantm=quant_re.match(s)
            printm=print_re.match(s)
            breakm=break_re.match(s)
            if trm:
                result_rules.append(
                    TRRule(trm.group(2),trm.group(3),trm.group(4),trm.group(1)))
                s=s[trm.end():].lstrip()
            elif spm:
                result_rules.append(
                    PRRule(spm.group(2),spm.group(3),spm.group(1)))
                s=s[spm.end():].lstrip()
            elif reqm:
                result_rules.append(ReqRule(reqm.group(1)))
                s=s[reqm.end():].lstrip()
            elif quantm:
                result_rules.append(QRule(quantm.group(1),quantm.group(2)))
                s=s[quantm.end():].lstrip()
            elif printm:
                result_rules.append(PrintRule(printm.group(1)))
                s=s[printm.end():].lstrip()
            elif breakm:
                result_rules.append(BreakRule())
                s=s[breakm.end():].lstrip()
            else:
                return len(s)
        return 0
    # end of subfunction 
    
    r=Rule()

    s=s.lstrip()
    applym=apply_spec_re.match(s)
    if applym:
        r.apply_spec=applym.group(1)
        debugmsg(s)
        s=s[applym.end(1):]
        debugmsg(s)

    o=separator.match(s)
    if not o:
        raise GTError("Parse error: '->' missing in rule '%s'" % s)
#        error("Parse error: '->' missing in rule '%s'" % s)
    slhs=o.group(1)
    srhs=o.group(2)

    # Parse the left-hand side of the rule
    n=parse_string(slhs,r.lhs)
    if n!=0:
        print "Parse error on the left hand side:"
        print slhs
        print "%s^" % (" "*(len(slhs)-n))
        sys.exit(2)
    # Parse the right-hand side of the rule
    n=parse_string(srhs,r.rhs)
    if n!=0:
        print "Parse error on the right hand side:"
        print srhs
        print "%s^" % (" "*(len(srhs)-n))
        sys.exit(2)
    return r

### End of Parsing #######################
##########################################

def create_datastructures(l):
    """
    Returns LstsData object which contains the following objects:

    set of Transition objects and
    set of Proposition objects

    In addition to that, four dictionaries are created which map
    items to list of elements in the sets above:

    tr_by_ss: source state -> list of transitions

    pr_by_st: state -> list of state propositions

    Every attribute of Transition and Proposition objects are strings.
    There is an annoying thing with quotes. Keys in tr_by_ss and
    pr_by_ss include quotation marks but attributes of Transition and
    Proposition objects do not.
    """
    if l==None: # create new single-state lsts data structure
        l=LstsData()
        istatesymbol='0'
        l.initial_state='"%s"' % istatesymbol
        l.tr=[]
        l.ac=[]
        l.pr=[Proposition(istatesymbol,'gt:istate')]
        l.tr_by_ss={l.initial_state:[]}
        l.pr_by_st={'"%s"'%istatesymbol:[l.pr[0]]}
        l.pr_hash={'"%s"'%l.pr[0].prop:1}
        return l

    istatesymbol='%s'%int(l.get_header().initial_states)
    initial_state='"%s"'%istatesymbol
    
    tr=[] # list of Transitions
    pr=[Proposition(istatesymbol,'gt:istate')] # list of Propositions
    ac=[] # list of action names (strings)

    tr_by_ss = {}
    pr_by_st = {'"%s"'%istatesymbol:[pr[0]]}
    pr_hash = {'"%s"'%pr[0].prop:1}

    actionnames=l.get_actionnames()
    for source,outtrans in enumerate(l.get_transitions()):
        tr_by_ss['"%s"'%source]=[]
        for dest,action in outtrans:
            a=actionnames[action]
            t=Transition(source,a,dest)
            tr.append( t )
            ss='"%s"'%source
            tr_by_ss[ss].append( t )
            if not '"%s"'%a in ac: ac.append('"%s"'%a)

    for propname in l.get_stateprops():
        for state in l.get_stateprops()[propname]:
            p=Proposition(state,propname)
            pr.append( p )
            pr_hash['"%s"'%propname]=pr_hash.get('"%s"'%propname,0)+1
            try: pr_by_st['"%s"'%state].append(p)
            except KeyError: pr_by_st['"%s"'%state]=[p]

    l=LstsData()
    l.tr=tr
    l.pr=pr
    l.ac=ac
    l.tr_by_ss=tr_by_ss
    l.pr_by_st=pr_by_st
    l.pr_hash=pr_hash
    l.initial_state=initial_state

    return l

def create_lsts(lstsdata, keep_actionnames=["tau"], keep_propositionnames=()):
    """
    Dual for create_datastructure: builds a new lsts object
    based on the given LstsData object.
    """
    newlsts=lsts.writer()

    actionnames=keep_actionnames[:]
    transitions=[[]]
    propositions=dict([(p,[]) for p in keep_propositionnames])
    first_state_symbol=lstsdata.initial_state
    found_states={first_state_symbol:0} # map state string in lstsdata to state number

    statestack=[first_state_symbol]

    while statestack:
        ss=statestack.pop()
        ssnum=found_states[ss]

        for t in lstsdata.tr_by_ss[ss]:
            if not t.action in actionnames:
                actionnames.append(t.action)
            acnum=actionnames.index(t.action)

            ds='"%s"'%t.dest
            
            if not ds in found_states:
                found_states[ds]=len(found_states)
                transitions.append([])
                if ds in lstsdata.tr_by_ss:
                    # there are leaving transitions from ds
                    statestack.append(ds)
            dsnum=found_states[ds]
            
            transitions[ssnum].append((dsnum,acnum))

    newlsts.set_actionnames(actionnames)
    newlsts.set_transitions(transitions)

    for st in lstsdata.pr_by_st:
        for pr in lstsdata.pr_by_st[st]:
            if st in found_states:
                if not pr.prop in ["gt:istate"]:
                    # reserved state propositions are not written to the lsts
                    if not pr.prop in propositions:
                        propositions[pr.prop]=[]
                    propositions[pr.prop].append(found_states[st])

    newlsts.set_stateprops(propositions)
    return newlsts

def copy_of_rule(origrule,attribute,newvalue):
    """
    Returns a copy of the origrule, where the given attribute
    is set to newvalue.
    """
    newrule=copy.copy(origrule)
    setattr(newrule,attribute,'%s' % newvalue)
    return newrule

def instantiate_trrule(lstsdata,r,which_hand_side,next_regex):
    """
    Returns a triplet:
    1. dictionary { symbol: list_of_new_values }
    2. list of instantiations of rule r
    3. the number of next regular expression
    
    If the dict is not empty, the syms in the dict should be instanted
    right away and then the same rule should be instantiated again. If
    the dict is empty, and the list includes a rule, the rule is
    already concrete, no further instantiations needed. If the list
    does not contain any rules, the rule does not match to any
    transition.
    """

    def expand_tr_position(position,r,lstsdata,which_hand_side,next_regex):
        """
        position = 'source', 'action' or 'dest'; r = rule
        returns retdict, retlist
        """
        retdict,retlist={},[]
        contents=getattr(r,position)
        # First, try if the position contains a variable name
        if re_variable_name.match(contents):
            if which_hand_side=='left':
                # It is; expand it to all possible values
                retdict[contents]=[]
                if position=='source':
                    for ss in lstsdata.tr_by_ss:
                        retdict[contents].append(ss)
                        retlist.append(copy_of_rule(r,position,ss))
                elif position=='action':
                    for t in lstsdata.tr_by_ss[r.source]:
                        retlist.append(copy_of_rule(r,position,
                                                    '"%s"' % t.action))
                        retdict[contents].append('"%s"' % t.action)
                elif position=='dest':
                    for t in lstsdata.tr_by_ss[r.source]:
                        if not r.action=='"%s"' % t.action: continue
                        retlist.append(copy_of_rule(r,position,
                                                    '"%s"' % t.dest))
                        retdict[contents].append('"%s"' % t.dest)
            elif which_hand_side=='right':
                # New variables in places of states on the right-hand side
                # mean creating a new state.
                if position in ['source','dest']:
                    newstate='"tr_state/%s"' % len(lstsdata.tr_by_ss)
                    lstsdata.tr_by_ss[newstate]=[]
                    retdict[contents]=[newstate]
                    retlist.append(copy_of_rule(r,position,newstate))
                else:
                    raise GTError("Cannot use free variable as the action " +
                                  "name on the right hand side: %s" % r)
#                    error("Cannot use free variable as the action name "+
#                          "on the right hand side: %s" % r)
        # Second, try if the position contains regular expressions
        elif re_regexps.search(contents):
            regex=convert_to_regexp(contents)
            if position=='source':
                ### * BAD THING *
                ### here I would like to use generators:
                ### elements=(s for s in lstsdata.tr_by_ss)
                ### but for compatibility with python 2.3
                ### I must use lists.
                elements=[s for s in lstsdata.tr_by_ss]
            elif position=='action':
                elements=['"%s"'%t.action for t in lstsdata.tr_by_ss[r.source]]
            elif position=='dest':
                elements=[t.dest for t in lstsdata.tr_by_ss[r.source]
                          if r.action==t.action]
            new_regexnum=next_regex
            for e in elements:
                m=regex.match(e)
                if m:
                    retlist.append(copy_of_rule(r,position,e))
                    new_regexnum=next_regex
                    for g in m.groups():
                        # for every ${} in the regexp create symbol
                        # $=n. and replace it by the contents of the
                        # group
                        try: retdict["$=%s." % new_regexnum].append(g)
                        except KeyError: retdict["$=%s." % new_regexnum]=[g]
                        new_regexnum+=1
            next_regex=new_regexnum
        else: # no variable, no regexps, so it should be a matching value
            pass
        return retdict,retlist,next_regex
    # end of function expand_position
    
    retdict={}
    retlist=[]

    rd,rl,next_regex=expand_tr_position('source',r,lstsdata,which_hand_side,next_regex)
    if rd: return rd,rl,next_regex
    else:
        if which_hand_side=='left':
            if not r.source in lstsdata.tr_by_ss:
                # debugmsg("No matching source state for rule '%s'" % r)
                # debugmsg("WAS: r.source=%s,%s" % (r.source,str(lstsdata.tr_by_ss.keys())))
                return {},[],next_regex
        # right-hand side can pass, when no symbol changes are required.
        # every value will be matched...

    rd,rl,next_regex=expand_tr_position('action',r,lstsdata,which_hand_side,next_regex)
    if rd: return rd,rl,next_regex
    else:
        if which_hand_side=='left':
            if not [t for t in lstsdata.tr_by_ss[r.source]
                    if r.action=='"%s"'%t.action ]:
                # debugmsg("No matching action for rule '%s'" % r)
                return {},[],next_regex

    rd,rl,next_regex=expand_tr_position('dest',r,lstsdata,which_hand_side,next_regex)
    if rd: return rd,rl,next_regex
    else:
        if which_hand_side=='left':
            if not [t for t in lstsdata.tr_by_ss[r.source]
                    if (r.action=='"%s"'%t.action) and (r.dest=='"%s"'%t.dest) ]:
                # debugmsg("No matching dest state for rule '%s'" % r)
                return {},[],next_regex
    
    # Now rule r specifies unambiguously a single transition
    return {},[r],next_regex


def instantiate_qrule(lstsdata,r,which_hand_side,next_regex):
    """
    returns retdict, retlist, next_regex
    """
    setdef=r.setdef.lower()
    if setdef in ['s','states']:
        retdict={r.variable: lstsdata.tr_by_ss.keys()}
        return retdict,[], next_regex
    elif setdef in ['a','actions']:
        retdict={r.variable: lstsdata.ac}
        return retdict,[], next_regex
    elif setdef in ['p','props','propositions']:
        retdict={r.variable: lstsdata.pr_hash.keys()}
        return retdict,[], next_regex

def instantiate_prrule(lstsdata,r,which_hand_side,next_regex):

    def expand_pr_position(position,r,lstsdata,which_hand_side,next_regex):
        """
        position = 'state' or 'prop'; r = rule
        returns retdict, retlist
        """
        retdict,retlist={},[]
        contents=getattr(r,position)
        # First, try if the position contains a variable name
        if re_variable_name.match(contents):
            if which_hand_side=='left':
                # It is; expand it to all possible values
                retdict[contents]=[]
                if position=='state':
                    # tr_by_ss contains symbols of all states,
                    # pr_by_st contains only states which have (had) props
                    for st in lstsdata.tr_by_ss:
                        retdict[contents].append(st)
                        retlist.append(copy_of_rule(r,position,st))
                elif position=='prop':
                    for p in lstsdata.pr_by_st.get(r.state,[]):
                        retlist.append(copy_of_rule(r,position,
                                                    '"%s"' % p.prop))
                        retdict[contents].append('"%s"' % p.prop)
            elif which_hand_side=='right':
                # New variables in places of states on the right-hand side
                # mean creating a new state.
                if position == 'state':
                    newstate='"pr_state/%s"' % len(lstsdata.tr_by_ss)
                    lstsdata.pr_by_st[newstate]=[] # this is a new proposition state
                    lstsdata.tr_by_ss[newstate]=[] # this is also a new state
                    retdict[contents]=[newstate]
                    retlist.append(copy_of_rule(r,position,newstate))
                else:
                    raise GTError("Cannot use free variable as proposition name "+
                          "on the right hand side: %s" % contents)
#                    error("Cannot use free variable as proposition name "+
#                          "on the right hand side: %s" % contents)
        # Second, try if the position contains regular expressions
        elif re_regexps.search(contents):
            regex=convert_to_regexp(contents)
            if position=='state':
                ### * BAD THING *
                ### see the previous bad thing.
                elements=[s for s in lstsdata.tr_by_ss] # take all states
            elif position=='prop':
                elements=['"%s"'%p.prop for p in lstsdata.pr_by_st.get(r.state,[])]
            new_regexnum=next_regex
            for e in elements:
                m=regex.match(e)
                if m:
                    retlist.append(copy_of_rule(r,position,e))
                    new_regexnum=next_regex
                    for g in m.groups():
                        # for every ${} in the regexp create symbol
                        # $=n. and replace it by the contents of the
                        # group
                        try: retdict["$=%s." % new_regexnum].append(g)
                        except KeyError: retdict["$=%s." % new_regexnum]=[g]
                        new_regexnum+=1
            next_regex=new_regexnum
        # no variable, no regexps, so it should be a matching value
        return retdict,retlist,next_regex
    # end of function expand_position

    rd,rl,next_regex=expand_pr_position('state',r,lstsdata,which_hand_side,next_regex)
    if rd: return rd,rl,next_regex
    else:
        if which_hand_side=='left':
            if not r.state in lstsdata.pr_by_st:
                return {},[],next_regex

    rd,rl,next_regex=expand_pr_position('prop',r,lstsdata,which_hand_side,next_regex)
    if rd: return rd,rl,next_regex
    else:
        if which_hand_side=='left':
            if not [p for p in lstsdata.pr_by_st[r.state]
                    if r.prop=='"%s"'%p.prop ]:
                return {},[],next_regex

    # Now rule r specifies unambiguously a single proposition
    return {},[r],next_regex

def instantiate_rule(lstsdata,absrule):

    def instantiate_symbol_in_element(element,symbol,replacement):
        replaced=0
        for str_attribute in element.string_slots:
            attrval=getattr(element,str_attribute)
            if (symbol[:2]=="$=" or isinstance(element,PrintRule) or isinstance(element,ReqRule))\
                   and symbol in attrval:
                # regexp replacement syms are replaced anywhere
                setattr(element,str_attribute,
                        attrval.replace(symbol,replacement))
                replaced+=1
            elif symbol==attrval:
                # variable-names are replaced only as is
                setattr(element,str_attribute,replacement)
                replaced+=1
        return replaced

    def instantiate_symbol(absrule,symbol,replacement):
        """
        Change lhs and rhs of absrule by replacing the symbol
        (variable-name or '$=n.') by the replacement.
        Returns the number of symbols that where replaced.
        """
        replaced=0
        for elt in absrule.lhs + absrule.rhs:
            replaced+=instantiate_symbol_in_element(elt,symbol,replacement)
        return replaced
                    
    # end of instantiate_symbol

    def copy_and_replace(rule,oldsubrule,newsubrule):
        """
        Returns a copy of rule where oldsubrule in lhs or rhs is
        replaced by newsubrule. If newsubrule is a list of rule
        elements, the elements will be inserted starting from the
        position of oldsubrule.
        """
        newrule=Rule()
        newrule.next_regex=rule.next_regex
        newrule.apply_spec=rule.apply_spec
        for subrule in rule.lhs:
            if subrule==oldsubrule:
                if type(newsubrule)==list: newrule.lhs.extend(newsubrule)
                elif newsubrule: newrule.lhs.append(newsubrule)
            else: newrule.lhs.append(copy.copy(subrule))
        for subrule in rule.rhs:
            if subrule==oldsubrule:
                if type(newsubrule)==list: newrule.rhs.extend(newsubrule)
                elif newsubrule: newrule.rhs.append(newsubrule)
            else: newrule.rhs.append(copy.copy(subrule))
        return newrule

    def remove_element(element,rule,side):
        if side=='left':rule.lhs.remove(element)
        else: rule.rhs.remove(element)

    ###  main of instantiate_rule
    abs_rules=[absrule]
    concrete_rules=[]
    concrete_rules_hash={}

    while abs_rules:
        if debugflag:
            msg_p1 = "abs_rules:%s\t" % os.linesep
            msg_p2 = "%s\t" % os.linesep
            debugmsg(msg_p1+msg_p2.join([str(r) for r in abs_rules]),2)

        absrule=abs_rules.pop()
        symchanges={}

        elements=[e for e in absrule.lhs+absrule.rhs]
        element_index=0
        last_element=len(elements)-1
        first_right_element_index=len(absrule.lhs)

        while element_index <= last_element:
            element=elements[element_index]
            if element_index<first_right_element_index: side='left'
            else: side='right'

            instantiate=None
            if element.is_abstract:
                if isinstance(element,TRRule):
                    instantiate=instantiate_trrule
                elif isinstance(element,PRRule):
                    instantiate=instantiate_prrule
                elif isinstance(element,QRule):
                    instantiate=instantiate_qrule
            elif isinstance(element,PrintRule):
                element.output()
                remove_element(element,absrule,side)
                element_index+=1
            elif isinstance(element,ReqRule):
                value=element.evaluate()
                if value:
                    remove_element(element,absrule,side)
                    element_index+=1
                else:
                    # requirement was not fulfilled =>
                    # forget this absrule.
                    break
            elif isinstance(element,BreakRule):
                sys.exit(0)
            else: # not abstract element
                element_index+=1

            if instantiate:
                symchanges,newelements,absrule.next_regex = \
                    instantiate(lstsdata,element,side,absrule.next_regex)
                if not symchanges:
                    if isinstance(element,QRule):
                        # It seems that someone is quantifying over an empty
                        # set. Bad.
                        raise GTError("Cannot quantify over an empty set. Rule: %s" % element)
#                        error("Cannot quantify over an empty set. Rule: %s" % element)
                    # we are dealing with a concrete element
                    if newelements and not element.neg:
                        # element matches and is not a negation,
                        # this is nice, continue to the next element
                        element.is_abstract=0
                        element_index+=1
                    elif newelements and element.neg:
                        # element matches but it is a negation, so it should
                        # not. this absrule must be forgotten.
                        break
                    elif not newelements and not element.neg:
                        # element does not match, even if it should.
                        # forget this rule.
                        break
                    elif not newelements and element.neg:
                        # element does not match and it should not match.
                        # remove the negated element so that it will not
                        # affect applying the rule.
                        remove_element(element,absrule,side)
                        element_index+=1
                else:
                    # it was not a concrete rule, let's instantiate symbols
                    if isinstance(element,QRule):
                        # there is only one symbol that needs to be replaced
                        # with a number of values.
                        sym=symchanges.keys()[0]
                        for v in symchanges[sym]:
                            abs_rules.append(copy_and_replace(absrule,
                                                              element, None))
                            instantiate_symbol(abs_rules[-1],sym,v)
                    elif not element.neg:
                        # if element was not negated, instantiation produces
                        # many absrules with the same number of elements
                        for i,newelement in enumerate(newelements):
                            abs_rules.append(copy_and_replace(absrule,
                                                              element,newelement))
                            for symbol in symchanges:
                                instantiate_symbol(abs_rules[-1],
                                                   symbol,symchanges[symbol][i])
                    else:
                        # if the element was negated, instantiation produces
                        # many (negated) elements in the same absrule
                        new_absrule=copy_and_replace(absrule,element,newelements)
                        # note that free variables in negative rules
                        # do not bound the value of the variable. in
                        # other words, the next occurence of the same
                        # variable will also be free. therefore, no
                        # symbol instantiating here.
                        abs_rules.append(new_absrule)
                    # this rule can now be forgotten,
                    # we just added a bit less abstract rule(s) to abs_rules.
                    break 
        else: # did not break out from while => absrule is concrete
            # add concrete rule if it is unique
            if not str(absrule) in concrete_rules_hash:
                concrete_rules_hash[str(absrule)]=1
                concrete_rules.append(absrule)
    if debugflag:
        msg_p1 = "concrete_rules:%s\t" % os.linesep
        msg_p2 = "%s\t" % os.linesep
        debugmsg(msg_p1+(msg_p2.join(["%s"%r for r in concrete_rules])),1)

    return concrete_rules


def apply_rules(rules,lstsdata):
    tr_hash,pr_hash={},{}
    for r in rules:
        for remove_obj in r.lhs:
            if isinstance(remove_obj,TRRule):
                ss,ac,ds=remove_obj.source,remove_obj.action,remove_obj.dest
                # Find and remove transition:
                for t in lstsdata.tr_by_ss[ss]:
                    if '"%s"'%t.action==ac and '"%s"'%t.dest==ds: break
                else: # for loop not breaked -> no transition found
                    continue
                # debugmsg("removing %s" % t)
                lstsdata.tr_by_ss[ss].remove(t)
            elif isinstance(remove_obj,PRRule):
                # Find and remove proposition from a state:
                for pr in lstsdata.pr_by_st[remove_obj.state]:
                    if '"%s"'%pr.prop==remove_obj.prop: break
                else: # for loop not breaked -> no proposition found.
                    continue

        for add_obj in r.rhs:
            if isinstance(add_obj,TRRule):
                ss,ac,ds=add_obj.source,add_obj.action,add_obj.dest
                # debugmsg("adding (%s,%s,%s)" % (ss,ac,ds))
                if not ac in lstsdata.ac: lstsdata.ac.append(ac)
                if not ss in lstsdata.tr_by_ss: lstsdata.tr_by_ss[ss]=[]
                if not ds in lstsdata.tr_by_ss: lstsdata.tr_by_ss[ds]=[]
                lstsdata.tr_by_ss[ss].append(Transition(ss[1:-1],ac[1:-1],ds[1:-1]))
            elif isinstance(add_obj,PRRule):
                st,pr=add_obj.state,add_obj.prop
                if not st in lstsdata.tr_by_ss: lstsdata.tr_by_ss[st]=[]
                lstsdata.pr_hash[pr]=lstsdata.pr_hash.get(pr,0)+1
                try: lstsdata.pr_by_st[st].append(Proposition(st[1:-1],pr[1:-1]))
                except KeyError: lstsdata.pr_by_st[st]=[Proposition(st[1:-1],pr[1:-1])]
    return lstsdata


def parse_args(argv):

    global version

    argv=argv[1:]

    # options
    arg_keep_labels = False
    arg_debugflag = False
    arg_input_file = None
    arg_output_file = None

    while argv:
        if argv[0] in ["--help","-help","-h"]:
            print __doc__
            sys.exit(1)
        elif argv[0] in ["--verbose","-v"]:
            arg_debugflag=True
        elif argv[0] in ["--version"]:
            print version
            sys.exit(1)
        elif argv[0] in ["--keep-labels"]:
            arg_keep_labels = True
        else: # the next might be a rule
            break
        argv=argv[1:]

    if len(argv)<2:
        print __doc__
        sys.exit(1)

    # input file
    if argv[0]=="-":
        arg_input_file = "-"
    elif argv[0].lower()=="new":
        if arg_keep_labels == 1:
            error("Option --keep-labels cannot be used with new lsts.")
        arg_input_file = None
    else:
        arg_input_file = argv[0]

    # output file
    if argv[1]=="-": 
        arg_output_file = argv[1]
    elif argv[1]=="none": 
        arg_output_file = None
    else:
        arg_output_file = argv[1]

    arg_rules = argv[2:]

    return (arg_input_file,arg_output_file,arg_keep_labels,arg_debugflag,arg_rules)

# MAIN
def gt(input_fileobj,output_fileobj,keep_labels,rules):
    outfile = output_fileobj
    if input_fileobj == None:
        inlsts = None
    else:
        try:
            inlsts=lsts.reader(input_fileobj)
        except Exception,e:
            raise GTError("Could not read input lsts from '%s'%s%s" % \
                              (str(input_fileobj),os.linesep,e))
#            error("Could not read input lsts from '%s'\n%s"%(input_fileobj.name,e))
    
    # the rest of command line arguments are handled as rules.

    all_rules=[parse_rulestr(s) for s in rules]
    
    next_lsts=inlsts

    # 1. Convert handled lsts to a handy datastructure
    lstsdata=create_datastructures( next_lsts )
    
    # Every rule will be handled separately
    # and applied in the order of appearance.    
    for rule in all_rules:

        if debugflag:
            debugmsg(str(lstsdata),1)

        if rule.apply_spec=='once:': # this is the default.
        
            # 2. Instantiate the rule to a set of concrete rules:
            # - free variables are given exact values
            # - regular expressions are matched and
            #   $=n. are replaced accordingly
            conc_rules=instantiate_rule(lstsdata,rule)

            # 3. Apply rules to the lsts, get a new lstsdata object
            lstsdata=apply_rules(conc_rules,lstsdata)

        elif rule.apply_spec=='repeat until no match:':
            while True:
                conc_rules=instantiate_rule(lstsdata,rule)
                if not conc_rules: break
                lstsdata=apply_rules(conc_rules,lstsdata)
            
    if outfile:
        if keep_labels == 1:
            outlsts=create_lsts(lstsdata, 
                                keep_actionnames=inlsts.get_actionnames(),
                                keep_propositionnames=inlsts.get_stateprops().keys())
        else:
            outlsts=create_lsts(lstsdata)
        outlsts.write(outfile)

if __name__=='__main__':
    input_filename,output_filename,keep_labels,arg_debugflag,rules = parse_args(sys.argv)

    if arg_debugflag:
        debugflag+=1

    infile = None
    outfile = None

    try:
        try:

            if input_filename == "-":
                infile = sys.stdin
            elif input_filename == None:
                infile = None
            else:
                infile = open(input_filename,'r')
            if output_filename == "-":
                outfile = sys.stdout
            elif output_filename == None:
                outfile = None
            else:
                outfile = open(output_filename,'w')

            gt(infile,outfile,keep_labels,rules)
        except GTError, e:
            error(e)
        except KeyboardInterrupt,e:
            sys.exit(1)
        except:
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    finally:
        if outfile and output_filename != "-":
            outfile.close()
        if infile and input_filename != "-":
            infile.close()
