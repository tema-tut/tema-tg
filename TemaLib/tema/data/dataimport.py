# coding: iso-8859-1
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
This module imports data file of form

'data-structure-spec', '[' value (, value)* ']'

Examples of data rows:

'phone_number', ['123 4567', '432 1567', '123 4765']

'address(name, street)', [('John','Smithstreet'), ('X','Unknown')]

'p(f1(f11,f12),f2)', [(('1a','1b'),'2'), (('1c', '1d'), '22')]

Comment lines start with #

Data module reads the following commandline arguments
(--data-args='name1:value1,...')

- file (string): name of the file from which data is loaded.
"""

# python standard:
import types
import copy
import random
import re

class DataEvaluationError(Exception): pass
class TestDataImportError(Exception): pass
class _DataError(Exception): pass

def _add_to_namespace(namespace, datarow):
    """
    Creates an object hierarchy where from
    d(f1,f2(f21,f22)), [(1, (100, 101)), (2, (200, 201))]
    follows
    d.f1 == [1,2]
    d.f2.f21 == [100,200]
    d.f2.f22 == [101,201]

    The hierarcy is added to the namespace.
    """

    class _DataCarrier(object):
        """
        Every variable and field is a data carrier. If a variable or a
        field v does not contain data (it is a container that includes
        subfields), str(v)=='<no data>', otherwise str(v) returns the
        current data value.
         """

        # __init__ and __call__ handle the parsing of the data structure
        # user input 'contact(firstname, lastname)' is transformed to expression
        # _DataCarrier('contact')(_DataCarrier('firstname'), _DataCarrier('lastname'))
        # which is then evaluated. The evaluation causes calling __init__ with
        # the name as parameter and __call__ with the subitems as parameters.
        def __init__(self, name):
            self._name = name
            self._children = ()
            self._values = []
            self._sval_to_index={}
            self._chosen = -1 # index to self._values list
            
        def __call__(self, *eltlist):
            if len(eltlist)==0: raise TestDataImportError("Fieldname missing")
            self._children = eltlist
            for e in self._children:
                if e._name in self.__dict__:
                    raise TestDataImportError("Multiple fields with name '%s'" % (e._name))
                self.__dict__[e._name] = e
            return self
        
        # _add_data is called with the data list as a parameter
        # For example, dc._add_data([('John', 'Smith'), ('Donald', 'Duck')])
        def _add_data(self, datarow):
            """at top level, datarow is [ tuple/str, tuple/str, ... ]"""
            if not self._children:
                self._chosen = 0
                self._values.append(datarow)
                self._sval_to_index[str(datarow)]=len(self._values)-1
            else:
                # print datarow, "to", self._name, ':', ', '.join(c._name for c in self._children)
                if type(datarow) not in (tuple, list) or len(self._children) != len(datarow):
                    raise TestDataImportError("Illegal number of data items: %s." % (datarow,))
                for i, child in enumerate(self._children): # data goes to children
                     child._add_data(datarow[i])

        # _DataCarrier._pick_matching
        def _pick_matching(self,coverage):
            picked=None
            if self._values:
                picked=coverage.pickDataValue(self._values)
            if picked==None:
                for d in dir(self):
                    if type(getattr(self,d))==_DataCarrier:
                        picked_index=getattr(self,d)._pick_matching(coverage)
                        if picked_index:
                            return picked_index
                else: # nothing was picked
                    return None
            return self._sval_to_index[picked]
                            
        # _DataCarrier._choose_any
        def _choose_any(self,coverage,new_value=None):
            """set every datacarrier to the same _chosen value"""
            if coverage and new_value==None:
                picked_index=self._pick_matching(coverage)
                if picked_index!=None: # spread out the picked value
                    for d in dir(self):
                        if type(getattr(self,d))==_DataCarrier:
                            getattr(self,d)._choose_any(None,picked_index)
                    self._chosen=picked_index
                    return picked_index
                # if nothing was picked, new_value==None, so we go random
            if new_value==None: # come up with a random value
                if self._values:
                    new_value=random.randint(0,len(self._values)-1)
                    for d in dir(self):
                        if type(getattr(self,d))==_DataCarrier:
                            getattr(self,d)._choose_any(None,new_value)
                    self._chosen=new_value
                    return new_value
                else:
                    for d in dir(self):
                        if type(getattr(self,d))==_DataCarrier:
                            new_value=getattr(self,d)._choose_any(None,new_value)
                    self._chosen=new_value
                    return new_value
            else: # new_value!=None
                self._chosen=new_value
                for d in dir(self):
                    if type(getattr(self,d))==_DataCarrier:
                        getattr(self,d)._choose_any(None,new_value)
                return new_value
            
        # _DataCarrier._choose_next
        def _choose_next(self,new_value=None):
            if new_value==None and self._values:
                if self._chosen+1 >= len(self._values): new_value=0
                else: new_value=self._chosen+1
            for d in dir(self):
                if type(getattr(self,d))==_DataCarrier:
                    new_value=getattr(self,d)._choose_next(new_value)
            self._chosen=new_value
            return new_value

        # _DataCarrier._choose_first
        def _choose_first(self):
            return self._choose_next(0)

        def __le__(self,other):
            if type(other)==int: return int(self)<=other
            if type(other)==str: return str(self)<=other
            if type(other)==float: return float(self)<=other
            if str(self)!="<no data>": return str(self)<=str(other)
            raise DataEvaluationError("Cannot compare '<=' of a structure.")
            
        def __eq__(self,other):
            if type(other)==int: return int(self)==other
            if type(other)==str: return str(self)==other
            if type(other)==float: return float(self)==other
            if self._values!=other._values: return False
            if self._chosen!=other._chosen: return False
            for d in dir(self):
                # attributes starting with _ do not affect equity of objects
                if d[:1]=='_': continue
                if type(getattr(self,d))==_DataCarrier:
                    if not hasattr(other,d) or type(getattr(other,d))!=_DataCarrier:
                        return False
                    if not (getattr(self,d)==getattr(other,d)):
                        return False
            # FIXME: datacarrier attributes (or at least their names)
            # should be stored to a separate set that would be an
            # attribute of self. In equality comparison, they should
            # be compared in both directions: does other have
            # everything that self has and in the other way around.
            return True
        def val(self):
            return self._values[self._chosen]
        def __str__(self):
            if len(self._values)>0:
                return str(self._values[self._chosen])
            else:
                return "<no data>"
        def __int__(self):
            s=str(self)
            if s=="<no data>": return s
            return int(s)
        def __float__(self):
            s=str(self)
            if s=="<no data>": return s
            return float(s)
        def __getitem__(self, index):
            return self._values[self._chosen][index]
        def __len__(self):
            return len(self._values[self._chosen])

    def create_hierarchy(structurespec, datavalues):
        """
        structurespec example: 'contact(name, address(street, city, country), phone)'
        datavalues example: [ ('Antti', ('XKatu', 'Tampere', 'Finland'), '045 631 xxxx') ]
        """
        try:
            evaluable_sspec = re.sub(r'([a-zA-Z][a-zA-Z0-9_]*)', '_DataCarrier("\\1")', structurespec)
            hierarchy = eval(evaluable_sspec,{'_DataCarrier': _DataCarrier})
        except Exception, e:
            raise TestDataImportError("Could not parse data hierarchy: %s. (%s)" % (e, structurespec))
        if type(datavalues) not in (tuple, list) or len(datavalues)==0:
            raise TestDataImportError("Data values missing")
        for datatuple in datavalues:
            hierarchy._add_data(datatuple)
        return hierarchy

    if len(datarow)!=2: raise TestDataImportError('Syntax error on row %s' % (datarow,))
    h = create_hierarchy(datarow[0], datarow[1])
    if h._name in namespace:
        raise _DataError("Identifier '%s' is already defined" % datarow[0])
    namespace[h._name] = h


class RuntimeData:

    def __init__(self):
        ### Functions available in namespace:
        # any returns a copy of a datacarrierobject
        def any(dco):
            dco._choose_any(self.namespace.get('_COV',None))
            return copy.deepcopy(dco)
        def next(dco):
            dco._choose_next()
            return copy.deepcopy(dco)
        def first(dco):
            dco._choose_first()
            return copy.deepcopy(dco)
        self.namespace={'any':any,'next':next,'first':first}

    def evalString(self,dataexpression,coverage=None):
        if coverage:
            self.namespace['_COV']=coverage
        try:
            exec(dataexpression,{},self.namespace)
        except Exception,msg:
            raise DataEvaluationError("Error %s when evaluating '%s': %s"
                                      % (type(msg),dataexpression,msg))
        if '_COV' in self.namespace:
            del self.namespace['_COV']
        
        if 'OUT' in self.namespace:
            retval=str(self.namespace['OUT'])
            del self.namespace['OUT']
        else:
            retval=""
        return retval
    
    def loadFromFile(self,fileobj):
        """
        Reads the given file object, returns dictionary that can be used
        as a part of the namespace where data expressions are evaluated.
        """
        for lineno, line in enumerate(fileobj): # read line by line
            line=line.replace(chr(0x0d),'')
            if len(line.strip())==0 or line[0]=="#": continue
            try: 
                # transformation: a(b,c): [ ... ] to 'a(b,c)', [ ... ]
                line = "('%s', %s\n)" % tuple(line.split(':',1))
                t=eval(line)
            except:
                raise TestDataImportError("Syntax error in line %s." % (lineno+1))
            if type(t)!=tuple or len(t)<2:
                raise TestDataImportError("Line %s: "
                                      % (lineno+1) +
                                      "too few elements, name and data are required.")
            if type(t[len(t)-1])!=list:
                raise TestDataImportError("Line %s: " % (lineno+1) + \
                                      "last element should be a list (in brackets [])")
            if [type(e) for e in t[1:-1]] != ([tuple]*len(t[1:-1])):
                raise TestDataImportError("Line %s: " % (lineno+1) + \
                                      "fieldspec should be a tuple (in parenthesis ())")
            try:
                _add_to_namespace(self.namespace,t)
            except _DataError,msg:
                raise TestDataImportError("Line %s: %s" % (lineno+1,msg))
        return self.namespace
