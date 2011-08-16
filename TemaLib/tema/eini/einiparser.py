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

test="""
# result['action']['1']['name'] == 'first action'
# result['property']['name']['value'] == 'test_of_new_file_format'


[pr/*

*/operty:value]

name: test_of_new_file_format
initial_state: 1
"""

import re

# ??? this DIFFERS from EINI-BNF:
# NAME is allowed to start with a number and _, because otherwise
# [action:action_name]
# 1: spam
# would produce an error ("1" is illegal name)
NAME='[a-zA-Z_0-9]\w*'
PURE_ESEP=':' # entity separator
PURE_FSEP=',' # field separator

OPENBR = '\s*\[\s*'
CLOSEBR = '\s*\]\s*'
ESEP='\s*'+PURE_ESEP+'\s*'
FSEP='\s*'+PURE_FSEP+'\s*'
FSEPre = re.compile(FSEP)

# the following elements are directly from EINI-BNF

# no_field_header: [ entityname ]
NO_FIELD_HEADER = re.compile(OPENBR+'('+NAME+')'+CLOSEBR+'$')

# list field header: [entityname:fieldname[]]
LIST_FIELD_HEADER = re.compile(OPENBR+'('+NAME+')'+ESEP+'('+NAME+')'+OPENBR+CLOSEBR+CLOSEBR+'$')

# str field header: [entityname: field1, field2, field3]
STR_FIELD_HEADER = re.compile(OPENBR+'('+NAME+')'+'('+ESEP+'('+NAME+')('+FSEP+'('+NAME+'))*)?'+CLOSEBR+'$')

INSTANCE_LIST = re.compile('\s*('+NAME+')\s*('+FSEP+NAME+')*\s*$')

# <STR_FIELD_DEFINITION> ::= <INSTANCE_NAME> ':' <STR_VALUE> ( ',' <STR_VALUE> )* <ENDL>
# <LIST_FIELD_DEFINITION>::= <INSTANCE_NAME> ':' [ <STR_VALUE> ( ',' <STR_VALUE> )* ] <ENDL>

X_FIELD_DEFINITION = re.compile('\s*('+NAME+')'+ESEP+'(.*)$')

class EiniParserException(Exception):
    pass

EPE_typemismatch="Type mismatch: field '%s' had type '%s', cannot make it '%s'."
EPE_sfderror="STR_FIELD_DEFINITION expected."
EPE_field_numbers="Data row should have %s fields. Found %s."
EPE_syntax_error="Syntax error."

comment_hash = re.compile("#[^\n]*")
comment_multiline = re.compile("/\*.*?\*/",re.DOTALL) # TODO! test '/' in /* */

def error(line,errmsg):
    raise EiniParserException("Eini parser error\n\ton line: '%s'\n\t%s"
                              % (line,errmsg))


def remove_comments(s):
    i=0
    len_s=len(s)
    results=[]
    while i < len_s:
        if s[i]=='#':
            i+=1
            while (i<len_s) and (s[i]!='\n'): i+=1
        elif s[i:i+2]=='/*':
            i+=2
            while (i<len_s) and (s[i:i+2]!='*/'): i+=1
            if s[i:i+2]=='*/': i+=2
        else:
            results.append(s[i])
            i+=1
    return "".join(results)

def escape(s):
    s=s.replace('\\#',chr(2)+'EINIESCAPED_hash'+chr(3))
    s=s.replace('\\/*',chr(2)+'EINIESCAPED_region'+chr(3))
    s=s.replace('\\,',chr(2)+'EINIESCAPED_comma'+chr(3))
    s=s.replace('\\\\',chr(2)+'EINIESCAPED_backslash'+chr(3))
    s=s.replace('\\ ',chr(2)+'EINIESCAPED_space'+chr(3))
    s=s.replace('\\0',chr(2)+'EINIESCAPED_emptystring'+chr(3))
    s=s.replace('\\N/A',chr(2)+'EINIESCAPED_N/A'+chr(3))
    return s

def unescape(s):
    if s==chr(2)+'EINIESCAPED_N/A'+chr(3):
        return None
    elif chr(2)+'EINIESCAPED_N/A'+chr(3) in s:
        raise error('\\N/A should be alone.',
                    EPE_syntax_error)
    else:
        s=s.replace(chr(2)+'EINIESCAPED_hash'+chr(3),'#')
        s=s.replace(chr(2)+'EINIESCAPED_region'+chr(3),'/*')
        s=s.replace(chr(2)+'EINIESCAPED_comma'+chr(3),',')
        s=s.replace(chr(2)+'EINIESCAPED_backslash'+chr(3),'\\')
        s=s.replace(chr(2)+'EINIESCAPED_space'+chr(3),' ')
        s=s.replace(chr(2)+'EINIESCAPED_emptystring'+chr(3),'')
        return s

def cleanstr(s):
    return unescape(s.strip())

class Entity(dict):
    def __init__(self,*a,**kw):
        dict.__init__(self,*a,**kw)
        self._fieldname_fieldtype_dict={}
        self._fields=self._fieldname_fieldtype_dict # FIX TODO: SHORT NAME FOR DEBUGGING

    def fields(self):
        return self._fieldname_fieldtype_dict

class Parser(object):

    def _complete(self,contents):
        # adds missing fields with data value None to the elements
        # which do not have fields
        c=contents
        for ent in c:
            ent_fields=c[ent].fields()
            for dkey in c[ent]:
                for f in ent_fields:
                    if c[ent][dkey]==None: c[ent][dkey]={}
                    if not f in c[ent][dkey]: c[ent][dkey][f]=None

    def parse(self,fileobj):

        def add_field(entityname,fieldname,fieldtype,d):
            """adds field to dictionary d of an entity"""
            if not entityname in d:
                d[entityname]=Entity()
            
            if fieldname==None: return
            
            if not fieldname in d[entityname]._fields:
                d[entityname]._fields[fieldname]=fieldtype
            else: # type already defined for the field, it must stay same
                if d[entityname]._fields[fieldname]!=fieldtype:
                    error('',EPE_typemismatch
                          % (fieldname,d[entityname]._fields[fieldname],fieldtype))
        # end of add_field

        result={}
        uncommented = remove_comments(escape(fileobj.read()))

        current_entity=None
        current_field_type=None
        current_fields=[]

        for line in uncommented.split('\n'):
            line=line.strip()

            if line=="": continue
            
            m=NO_FIELD_HEADER.match(line)
            if m:
                current_entity=m.group(1)
                current_field_type=None
                current_fields=[]
                add_field(current_entity,None,None,result)
                continue
            
            m=LIST_FIELD_HEADER.match(line)
            if m:
                current_entity=m.group(1)
                current_field_type=list
                current_fields=[m.group(2)]
                add_field(current_entity,m.group(2),current_field_type,result)
                continue

            m=STR_FIELD_HEADER.match(line)
            if m:
                current_entity=m.group(1)
                current_field_type=str
                current_fields=[]
                if m.group(2)==None: # no fields: [only_entity]
                    current_fields=[]
                    add_field(current_entity,None,None,result)
                else: # at least one field: [entity:field1,field2]
                    for fieldspec in m.group(2)[1:].split(PURE_FSEP):
                        this_field=fieldspec.strip()
                        current_fields.append(fieldspec.strip())
                        add_field(current_entity,this_field,str,result)
                        del this_field
                if not current_entity in result: result[current_entity]={}
                continue

            m=INSTANCE_LIST.match(line)
            if m:
                if current_field_type!=None:
                    error(line,EPE_syntax_error)
                for fieldspec in m.group(0).split(PURE_FSEP):
                    this_field=fieldspec.strip()
                    if not this_field in result[current_entity]:
                        result[current_entity][this_field]={}
                continue

            m=X_FIELD_DEFINITION.match(line)
            if m:
                data_key=m.group(1).strip()
                if not data_key in result[current_entity]:
                    result[current_entity][data_key]={}
                if current_field_type==str:
                    # try to read STR_FIELD_DEFINITION
                    if m.group(2).strip()=="":
                        error(line,EPE_sfderror)
                    field_data=FSEPre.split(m.group(2))
                    if len(field_data)!=len(current_fields):
                        error(line,EPE_field_numbers % (len(current_fields),
                                                        len(field_data)))
                    for i,value in enumerate(field_data):
                        result[current_entity][data_key][current_fields[i]]=cleanstr(value)
                    continue
                if current_field_type==list:
                    # try to read LIST_FIELD_DEFINITION
                    if not current_fields[0] in result[current_entity][data_key]:
                        result[current_entity][data_key][current_fields[0]]=[]
                    field_data=FSEPre.split(m.group(2))
                    for value in field_data:
                        if value.strip()=='': continue
                        result[current_entity][data_key][current_fields[0]].append(
                            cleanstr(value))
                    continue
                assert("code should have continued before this line"==0)
            error(line,EPE_syntax_error)
        self._complete(result)
        return result
