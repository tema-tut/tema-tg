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
clparser.requirement( coverage_language_expression )

returns requirement object (either elementary or combined requirement)
corresponding to the coverage language expression.

"""

# tema libraries:
import tema.coverage.coverage as coverage
# python standard:
import re

# operators listed in the order of precedence
# (the first binds most loosely)

OPERATORS=["or","and","then"]

ACTIONSHORTHANDS=["action","actions"]

VALUESHORTHANDS=["value","values"]

RESERVED=OPERATORS+ACTIONSHORTHANDS+VALUESHORTHANDS

class ParseError(Exception):
    pass

class ParseTreeNode:
    def __init__(self,parent=None,children=None,string="",item=None):
        self.parent=parent
        self.children=children
        self.string=string
        self.item=item
        # automatically add this node to the children of the parent
        if parent!=None: 
            parent.children.append(self)

    # The rest of the methods are for testing
    def dumps(self,indent=""):
        s=indent+self.string+'\n'
        for c in self.children:
            s+=c.dumps(indent+'\t')
        return s

    def __str__(self):
        return self.dumps()

    def equal_strings(self,other):
        childcount=len(self.children)
        return self.string==other.string and \
                   childcount==len(other.children) and \
                   [self.children[i].equal_strings(other.children[i])
                    for i in range(childcount)]==[True]*childcount

# Operators in parse tree are stored inside OperatorItem objects
class OperatorItem:
    def __init__(self,name):
        self.name=name.lower()
    def __lt__(self,other):
        if not isinstance(other,OperatorItem):
            raise TypeError("Operator item compared to %s." % type(other))
        return OPERATORS.index(self.name)<OPERATORS.index(other.name)
    def __str__(self):
        return self.name
    def getOperator(self):
        return OPERATORS.index(self.name)


class ERParser:
    """Parser for Elementary Requirements"""
    def __init__(self,model):
        if model:
            self._actionstrings=[ a.toString() for a in model.getActions() ]
        else:
            self._actionstrings=None

    def _expand_action_regexp(self,regexp):
        """If model was given in the constructor (that is,
        _actionstrings is set), we expand action regexp to explicit
        action names. Otherwise just return [regexp].

        Effect: when expanded,

        actions branch.*

        requires that every action with branch prefix must be
        executed. If not expanded, the same would require that an
        action with branch prefix and an action with loop prefix must
        be executed.

        value 1,2,3

        requires that at least one of the values 1, 2 and 3 is used.
        """
        
        if self._actionstrings: # expand item regexp
            regexplist=[]
            for a in self._actionstrings:
                if regexp.match(a):
                    regexplist.append(re.compile(re.escape(a)))
                    self.log("    %s" % a)
        else:
            regexplist=[regexp]
        return regexplist
            
    def parse(self,slist):
        """Parses first n strings in the string list slist. Returns
        either (None,slist) if the list does not begin with an
        elementary requirement; or (ElementaryRequirement-object,
        rest_of_slist), if an elementary requirement was
        found. rest_of_slist is the parameter list without elementary
        requirement.
        """
        
        # Elementary requirement consists of at least two elements: a
        # short-hand notation and a regular expression (which should
        # not be among the reserved words).
        if len(slist)<2 or slist[1] in RESERVED:
            return None,slist

        # Should the items be compiled to regular expressions?
        if slist[0] in ACTIONSHORTHANDS:
            try:
                itemregexp=re.compile(slist[1])
            except:
                raise ParseError("'%s' is not a valid regular expression" % slist[1])

        # short-hand notation:
        # action REGEXP  <=> any value >= 1 for actions REGEXP
        # actions REGEXP <=> every value >= 1 for actions REGEXP
        
        if slist[0]==ACTIONSHORTHANDS[0]:
            q=coverage.Query()
            q.setItemType(coverage.eqiAction)

            self.log("%s '%s' matches to:" % (ACTIONSHORTHANDS[0],slist[1]))
            q.setItemRegExps(self._expand_action_regexp(itemregexp))
            
            er=coverage.ElementaryRequirement()
            er.setQuery(q)
            er.setLowerBoundRequirement(coverage.eqqAny,1)
            return er,slist[2:]
        
        elif slist[0]==ACTIONSHORTHANDS[1]:
            q=coverage.Query()
            q.setItemType(coverage.eqiAction)

            self.log("%s '%s' matches to:" % (ACTIONSHORTHANDS[0],slist[1]))
            q.setItemRegExps(self._expand_action_regexp(itemregexp))
            
            er=coverage.ElementaryRequirement()
            er.setQuery(q)
            er.setLowerBoundRequirement(coverage.eqqAll,1)
            return er,slist[2:]

        elif slist[0]==VALUESHORTHANDS[0]:
            q=coverage.Query()
            q.setItemType(coverage.eqiValue)
            valuelist=slist[1].split(',')
            self.log("use at least one of values: %s" % str(valuelist))
            q.setItemRegExps(valuelist)
            er=coverage.ElementaryRequirement()
            er.setQuery(q)
            er.setValueCoverageRequirement(coverage.eqqAny,valuelist)
            return er,slist[2:]
            
        elif slist[0]==VALUESHORTHANDS[1]:
            q=coverage.Query()
            q.setItemType(coverage.eqiValue)
            valuelist=slist[1].split(',')
            self.log("use all values: %s" % str(valuelist))
            q.setItemRegExps(valuelist)
            er=coverage.ElementaryRequirement()
            er.setQuery(q)
            er.setValueCoverageRequirement(coverage.eqqAll,valuelist)
            return er,slist[2:]

        else:
            return None,slist


class CRParser:
    """Parser for Combined Requirements;
    CR ::= ER | CR (and|or|then) CR | "(" CR ")"
    """

    def _cleanup_tree(self,treenode):
        """Called after parsing. Checks that all parentheses have been
        matched, removes parentheses nodes, raises parse error if
        there are leafnodes without elementary criteria (for example,
        caused by 'actions a and ()') ."""
        # find the root
        while treenode.parent: treenode=treenode.parent
        rootnode=treenode
        if len(rootnode.children)==0:
            raise ParseError("Empty coverage requirement")

        # check tree validity, remove parentheses
        node_stack=[rootnode]
        while node_stack:
            node=node_stack.pop()
            if node.string=="(":
                raise ParseError("Unmatched '('.")
            if isinstance(node.item,OperatorItem):
                if len(node.children)<2:
                    raise ParseError("Too few parameters for operator '%s'" % node.item.name)
            node_stack.extend(node.children)
            if node.string=="()":
                if len(node.children)==0:
                    raise ParseError("Empty parenthesis")
                # remove node from tree, keep the order of node's parents children
                newchildren=[]
                for c in node.parent.children:
                    if c!=node:
                        newchildren.append(c)
                    else:
                        newchildren.extend(node.children)
                node.parent.children=newchildren
                node.children=[]

    def parse(self,slist,treenode,erparser):
        if (hasattr(self,"original_string")):
            self.log("Coverage requirement: %s" %
                     self.original_string)
            
        """Parses the strings in the slist. Returns parse tree."""
        if len(slist)==0:
            self._cleanup_tree(treenode)
            return

        if slist[0]=="(": ### OPEN PARENTHESES
            if not treenode.string in ["ROOT","("] + OPERATORS:
                raise ParseError("Cannot open parentheses here: '%s'" % " ".join(slist[:5]))
            self.parse(slist[1:],
                  ParseTreeNode(parent=treenode,children=[],string=slist[0]),
                  erparser)
            
        elif slist[0]==")": ### CLOSE PARENTHESES
            # search for the last open parentheses
            # continue parsing from that treenode
            while treenode.string!="(":
                treenode=treenode.parent
                if not treenode:
                    raise ParseError("Unmatched ')': '%s...'" % " ".join(slist[:5]))
            
            treenode.string+=")"
            self.parse(slist[1:],
                       treenode,
                       erparser)

        elif slist[0].lower() in OPERATORS: ### OPERATOR
            if not (isinstance(treenode.item,coverage.ElementaryRequirement)
                    or treenode.string=="()"):
                raise ParseError("Operator not expected: '%s...'" % " ".join(slist[:5]))
            operitem=OperatorItem(slist[0])

            # We go towards the root in the parse tree until we find a
            # node whose parent is 1) ROOT, 2) open parentheses or 3)
            # an operator with equal or lower precedence. Replace that
            # node with this operator.

            while not treenode.parent.string in ["ROOT","("] \
                  and \
                  not (treenode.parent.string in OPERATORS \
                       and treenode.parent.item<operitem):
                treenode=treenode.parent

            newnode=ParseTreeNode(parent=treenode.parent,
                                  children=[treenode],
                                  string=str(operitem),
                                  item=operitem)
            treenode.parent=newnode
            newnode.parent.children.remove(treenode)
            self.parse(slist[1:],newnode,erparser)

        else: ### ELEMENTARY REQUIREMENT
            # try if slist starts with Elementary Requirement
            # parent should be either root without other children or operator
            if (not treenode.string in OPERATORS) and \
               (not treenode.string in ["ROOT", "("]):
                #(len(treenode.children)>0):
                raise ParseError("Operator expected before: '%s...'" % " ".join(slist[:5]))
            er,rest=erparser.parse(slist)
            if not er:
                raise ParseError("Syntax error: '%s...'" % " ".join(slist[:5]))
            newnode=ParseTreeNode(parent=treenode,
                                  children=[],
                                  string=" ".join(slist[:len(slist)-len(rest)]),
                                  item=er)
            self.parse(rest,newnode,erparser)
            
                

def _split_to_slist(s):
    """Splits coverage language string to a list of strings. Here we
    make sure that parentheses () will be separate items in list.
    ???Consider: it would be better to separate only those parentheses
    which are not escaped with backslash; this would allow using
    (escaped) parentheses in the regular expressions."""
    return s.replace("("," ( ").replace(")"," ) ").split()


def _Replace_Operators_with_CombinedRequirements(node):
    """Overwrite item-fields of Operator tree nodes with
    corresponding CombinedRequirements"""
    for child in node.children: # go to leaf nodes
        _Replace_Operators_with_CombinedRequirements(child)

    # Now every item of the children is either ElementaryRequirement
    # or CombinedRequirement. If this node includes Operator, make it
    # CombinedRequirement. Otherwise this node must be
    # ElementaryRequirement.
    if isinstance(node.item,OperatorItem):
        cr=coverage.CombinedRequirement()
        cr.setOperator(node.item.getOperator())
        cr.setRequirements( [c.item for c in node.children] )
        node.item=cr
    elif not isinstance(node.item,coverage.ElementaryRequirement)\
             and not node.string=="ROOT":
        print "What the hexx is this?",node.item
        raise "HEXXISH ERROR"

def parse(s,model=None):
    """This function is mostly for internal and testing use. To get
    the requirement of the coverage language expression, use
    the requirement function."""
    crparser=CRParser()
    erparser=ERParser(model)

    # Make beautiful log entries (all parsers write 'Coverage:')
    # log method is plugged to requirement function by main program
    if hasattr(requirement,'log'):
        class Coverage: pass
        dummycoverage=Coverage()
        logfunc=lambda msg: requirement.log(dummycoverage,msg)
        crparser.log=logfunc
        erparser.log=logfunc
    else:
        crparser.log = lambda msg: None
        erparser.log = lambda msg: None

    rootnode=ParseTreeNode(string="ROOT",children=[])
    slist=_split_to_slist(s)
    crparser.original_string=s
    crparser.parse(slist,rootnode,erparser)
    return rootnode

def requirement(s,model=None):
    """Returns requirement object (either elementary or combined
    requirement) corresponding to the coverage language expression."""
    rootnode=parse(s,model)
    _Replace_Operators_with_CombinedRequirements(rootnode)
    return rootnode.children[0].item
