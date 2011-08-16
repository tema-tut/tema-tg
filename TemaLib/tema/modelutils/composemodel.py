#!/usr/bin/env python
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

"""Model composer.

Usage: tema.composemodel [configuration_file]

If configuration_file not given, read configuration from 'compose.conf'.
If configuration_file is '-', read configuration from standard input.
"""

from __future__ import with_statement

import shutil
import os
import re
import sys
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from tema.modelutils import PC_RULES_PATH,generatetaskswitcher,gt,rextendedrules,renamerules,specialiser
import tema.eini.einiparser as einiparser

_no_layout_rules=['T(s0,"kw_return true",s1)T(s1,"end_aw${.*}",s2)->T(s0,"end_aw$=1.",s2)', 'T(s0,"kw_return false",s1)T(s1,"end_aw${.*}",s2)->T(s0,"~end_aw$=1.",s2)']
_awgt_single_rules=['P(s0,"sv${.*}") -> P(s0,"sv$=1.") T(s0,"start_sv$=1.",s1) T(s1,"end_sv$=1.",s0)', 'T(s0,"aw${.*}",s1)T(s0,"~aw$=1.",s2) -> T(s0,"start_aw$=1.",s_new)T(s_new,"end_aw$=1.",s1)T(s_new,"~end_aw$=1.",s2)',	'T(s0,"aw${.*}",s1)->T(s0,"start_aw$=1.",s_new)T(s_new,"end_aw$=1.",s1)', 'T(s0,"WAKEts",s1) -> T(s0,"WAKEtsCANWAKE",s_new) T(s_new,"WAKEtsWAKE",s1)', 'P(s0,"SleepState") P(s1,"ta${.*}") -> P(s0,"SleepState") P(s1,"ta$=1.") T(s0,"ALLOW<$=1.>",s1)']
_awgt_multi_rules=['P(s0,"sv${.*}") -> P(s0,"sv$=1.") T(s0,"start_sv$=1.",s1) T(s1,"end_sv$=1.",s0)','T(s0,"aw${.*}",s1)T(s0,"~aw$=1.",s2) -> T(s0,"start_aw$=1.",s_new)T(s_new,"end_aw$=1.",s1)T(s_new,"~end_aw$=1.",s2)', 'T(s0,"aw${.*}",s1)->T(s0,"start_aw$=1.",s_new)T(s_new,"end_aw$=1.",s1)', 'T(s0,"WAKEts",s1) -> T(s0,"WAKEtsCANWAKE",s_new) T(s_new,"WAKEtsWAKE",s1)']

def error(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(1)

def combined_rules(targetdir,filename,mt_rules,rules_files):
    print "Generating combined multitarget rulesfile: %s" % filename
    contents = []
    for target in rules_files:
        filu = os.path.join(targetdir,target,rules_files[target])
        with open(filu) as input_handle:
            contents.extend(input_handle.readlines())

    with open(os.path.join(targetdir,mt_rules),'r') as input_handle:
        contents.extend(input_handle.readlines())

    l = list(set(contents))
    l.sort()
    l.reverse()
    sed_re = re.compile(r'^\(([a-zA-Z0-9_]*)/([^/]*),(.*)-> "(\2)')
    with open(os.path.join(targetdir,filename),'w') as output_handle:
        for line in l:
            line_fixed =sed_re.sub(r'(\1/\2,\3-> "\1/\4',line)
            output_handle.write("%s" % (line_fixed))

def mt_rules_ext(targetdir,rext_file):

    outputfile = "multitarget-rules.ext"
    inputfile = os.path.join(targetdir,rext_file)
    print "Generating %s" % outputfile

    out_fileobj = StringIO()
    with open(inputfile,'r') as in_fileobj:
        try:
            rextendedrules.rextendedrules(targetdir,False,in_fileobj,out_fileobj)
        except rextendedrules.RextendedrulesError,e:
            raise

    out_fileobj.seek(0)

    with open(os.path.join(targetdir,outputfile),'w') as output_handle:
        renamerules.rename_rules(None,out_fileobj,output_handle)

    out_fileobj.close()
    return outputfile

def mt_rules_rext(targetdir,rules_files):
    outputfile = "multitarget-rules.rext"
    print "Generating %s" % outputfile
    with open(os.path.join(targetdir,outputfile),'w') as output_handle:
        for target in rules_files:
            with open(os.path.join(targetdir,target,rules_files[target]),'r') as input_handle:
                _line_re = re.compile('^%s/.+="' % target)
                for line in input_handle:
                    if _line_re.match(line):
                        output_handle.write(line)
                    
        output_handle.write('TargetSwitcher="TargetSwitcher-awgt.lsts"%s' % os.linesep)
        output_handle.write('TargetSwitcher-rm="TargetSwitcher-rm.lsts"%s' % os.linesep)
        output_handle.write('Synchronizer="Synchronizer-awgt.lsts"%s' % os.linesep)
        output_handle.write('Synchronizer-rm="Synchronizer-rm.lsts.nolayout"%s' % os.linesep)
        pc_rule = os.path.join(PC_RULES_PATH,"GenericPCRules-Multitarget")
        with open(pc_rule,'r') as input_handle:
            output_handle.write(input_handle.read())
        return outputfile

def transform_rules_ext(targetdir,target,rules_file):
    print "Transforming rules-file: %s%s%s" % (target,os.sep,rules_file)
    name_orig = os.path.join(targetdir,"%s.orig" % (rules_file,))
    name_new = os.path.join(targetdir,rules_file)
    shutil.copy(name_new,name_orig)

    with open(name_orig,'r') as input_file:
        with open(name_new,'w') as output_file:
            renamerules.rename_rules(target,input_file,output_file)
    return

def targetswitcher(refinement_machine,targetdir,targets,substitutions):

    if refinement_machine:
        name = "TargetSwitcher-rm"
        print "Generating TargetSwitcher-rm: %s" % (name)
        type_param = "rm"
    else:
        name="TargetSwitcher"
        print "Generating TargetSwitcher: %s" % (name)
        type_param = "am"

    handle = StringIO()
    generatetaskswitcher.main(targetdir,type_param,None,targets,handle)
    handle.flush()
    handle.seek(0)
    taskswitcher = handle.readlines()
    handle.close()

    outputfile=os.path.join(targetdir,"%s.lsts" % name)
    with open(outputfile,'w') as handle:
        for line in taskswitcher:
            for subs in substitutions:
                line = subs[0].sub(subs[1],line)
            handle.write(line)

    return name

def am_awgt(targetdir,inputfile,transform_rules,keep_labels):
    outputfile = "%s-awgt.lsts" % inputfile.rsplit(".",1)[0]
    print "Action machine graphtrans: %s -> %s" % (inputfile,outputfile)

    with open(os.path.join(targetdir,inputfile)) as infile:
        with open(os.path.join(targetdir,outputfile),'w') as outfile:
            graphtrans(infile,outfile,transform_rules,keep_labels)

    return outputfile

def rules_ext(targetdir,rext_file,ext_file):
    print "Generating rules-file: %s -> %s" % (rext_file,ext_file)
    inputfile = os.path.join(targetdir,rext_file)
    outputfile = os.path.join(targetdir,ext_file)
    with open(inputfile,'r') as in_fileobj:
        with open(outputfile,'w') as out_fileobj:
            try:
                rextendedrules.rextendedrules(targetdir,False,in_fileobj,out_fileobj)
            except rextendedrules.RextendedrulesError,e:
                raise

def rules_rext(targetdir,action_machines,refinement_machines,target_type):
    print "Generating rules.rext-file: %s" % ("rules.rext")
    outputfile = os.path.join(targetdir,"rules.rext")
    target_strip = len(target_type) + 1
    with open(outputfile,'w') as handle:
        for am in action_machines:
            handle.write('%s = "%s-awgt.lsts"%s' % (am,am,os.linesep))
        for ref in refinement_machines:
            base = ref[target_strip:].replace("-rm.lsts.nolayout","-rm.nolayout")
            handle.write('%s = "%s"%s' % (base,ref,os.linesep))
        pc_rule = os.path.join(PC_RULES_PATH,"GenericPCRules")
        with open(pc_rule,'r') as input_handle:
            handle.write(input_handle.read())

    return "rules.rext"

def taskswitcher(refinement_machine,targetdir,actionmachines,target,name):
    if refinement_machine:
        print "Generating TaskSwitcher-rm: %s" % (name)

        full_name="/".join((target,"%s.lsts.nolayout" % name))
        outputfile=os.path.join(targetdir,full_name)
        type_param = "rm"
    else:
        full_name = name
        outputfile=os.path.join(targetdir,"%s.lsts" % name)
        if target:
            print "Generating multitarget TaskSwitcher: %s" % (name)
            type_param = "amtgts"
        else:
            print "Generating TaskSwitcher: %s" % (name)
            type_param = "am"

    with open(outputfile,'w') as handle:
        # TODO: Retval
        generatetaskswitcher.main(targetdir,type_param,target,actionmachines,handle)
    return full_name

def graphtrans(inputfile,outputfile,transform_rules,keep_labels):
    contents = inputfile.read()
    try:
        contents = unicode(contents,"utf-8").encode("iso-8859-1")
    except UnicodeDecodeError:
        pass

    try:
        contents_in = StringIO(contents)
        try:
            gt.gt(contents_in,outputfile,keep_labels,transform_rules)
        except gt.GTError,e:
            raise
    finally:
        contents_in.close()

def specialise(targetdir,actionmachine):
    infofile = "%s.info" % actionmachine
    lstsfile = "%s.lsts" % actionmachine
    print "Specialising action machine: %s" % actionmachine
    with open(os.path.join(targetdir,infofile),'r') as in_handle:
        with open(os.path.join(targetdir,lstsfile),'w') as out_handle:
            try:
                specialiser.specialiser(targetdir,in_handle,out_handle)
            except specialiser.SpecialiserError:
                raise
    return lstsfile

def rm_nolayout(targetdir, input_filename, keep_labels ):
    output_filename = ".".join((input_filename,"nolayout"))
    print "Refinement machine graphtrans: %s -> %s" % (input_filename,output_filename)

    with open(os.path.join(targetdir,input_filename),'r') as input_handle:
        with open(os.path.join(targetdir,output_filename),'w') as output_handle:
            graphtrans(input_handle,output_handle,_no_layout_rules,keep_labels)
            
    return output_filename
                      
def create_device(targetdir,target_type,actionmachines,result_file,multipart,target_name,taskswitcher_info):
    rm_list = []
    am_list = []
    actionmachines.sort()
    for am in actionmachines:
        am_base = am.rsplit('.',1)[0]
        rm = "/".join((target_type,"%s-rm.lsts" % am_base))
        #rm = os.path.join(target,"%s-rm.lsts" % am_base)
        if am_base.endswith("Specific") or am_base.endswith("SpecificTarget"):
            specialise(targetdir,am_base)
        if os.path.isfile(os.path.join(targetdir,rm)):
            rmnolayout = rm_nolayout(targetdir,rm,True)
            rm_list.append(rmnolayout)
        amawgt = am_awgt(targetdir,am,_awgt_single_rules,True)
        am_list.append(am_base)
    if taskswitcher_info[0]:
        if multipart:
            ts_target_name = target_name
        else:
            ts_target_name = None
        ts_name = taskswitcher(False,targetdir,am_list,ts_target_name,taskswitcher_info[0])
        ts_awgt = am_awgt(targetdir,"%s.lsts" % ts_name,_awgt_single_rules,True)
        # NOTE: Added first to am_list so that we can get comparable list to 
        # old  Makefile-based model-composing. Can be safely removed.
        am_list.reverse()
        am_list.append(ts_name)
        am_list.reverse()
        ts_rm = taskswitcher(True,targetdir,am_list,target_type,taskswitcher_info[1])
        rm_list.append(ts_rm)

    rules_rext_file = rules_rext(targetdir,am_list,rm_list,target_type)
    rules_ext(targetdir,rules_rext_file,result_file)
    return (rm_list,am_list)

def create_runnable(result,targetdir,multipart=False):
    type = result['general']['type']['value']
    result_file = result['general']['result']['value']
    if type == "multi":
        # Multi-type models are same as Main-level makefile on Makefile-based
        # model composing
        rules_files = {}
        for target in result['targets']:
            conffile = result['targets'][target]['conffile']
            targetdir_subpart = os.path.join(targetdir,target)
            result_subpart = einiparser.Parser().parse(open(os.path.join(targetdir_subpart,conffile)))
            rules_file_subpart = result_subpart['general']['result']['value']
            rules_files[target] = rules_file_subpart
            create_runnable(result_subpart,targetdir_subpart,True)
            transform_rules_ext(targetdir_subpart,target,rules_file_subpart)

        subs = [(re.compile(r"SLEEPts"),r"SLEEPtgts"),(re.compile(r"WAKEts"),r"WAKEtgts")]

        targetsw = targetswitcher(False,targetdir,result['targets'],subs)

        subs = [(re.compile(r"LaunchApp '([^']*)'"),r"SetTarget $(OUT=\1.id)$")]
        targetsw_rm = targetswitcher(True,targetdir,result['targets'],subs)

        rmnolayout = rm_nolayout(targetdir,"Synchronizer-rm.lsts",False)
        amawgt = am_awgt(targetdir,"Synchronizer.lsts",_awgt_multi_rules,False)
        amawgt = am_awgt(targetdir,"TargetSwitcher.lsts",_awgt_multi_rules,False)

        mt_rext = mt_rules_rext(targetdir,rules_files)
        mt_ext = mt_rules_ext(targetdir,mt_rext)
        combined_rules(targetdir,result_file, mt_ext,rules_files)

    elif type == "single":        
        # Single-type models are same as device-specific makefiles in Makefile-
        # based model composing
        taskswitchergen = result['general'].get('taskswitchergen',None)
        if taskswitchergen:
            taskswitchergen = taskswitchergen['value']
        taskswitchergenrm = result['general'].get('taskswitchergenrm',None)
        if taskswitchergenrm:
            taskswitchergenrm = taskswitchergenrm['value']
        for target in result['targets']:
            device_type = result['targets'][target]['type']
            target_am = result['targets'][target]['actionmachines']
            rm_list,am_list = create_device(targetdir,device_type,target_am,result_file,multipart,target,(taskswitchergen,taskswitchergenrm))

def compose_model(targetdir, conf_file):
    if os.path.isfile(os.path.join(targetdir,conf_file)):
        with open(os.path.join(targetdir,conf_file),'r') as input:
            result = einiparser.Parser().parse(input)
    elif conf_file == "-":
        result = einiparser.Parser().parse(sys.stdin)
    else:
        print >>sys.stderr, "Error: Configuration file '%s' not found." % conf_file
        return False
        
#    result['targets'], result['general']
#    assert('type' in result['targets'].fields())
#    assert('actionmachines' in result['targets'].fields())

    create_runnable(result,targetdir)
    return True
    

def _main():

    if len(sys.argv) == 2:
        if sys.argv[1] in ["-h","--help"]:
            print __doc__
            sys.exit(0)
        conf_file = sys.argv[1]
    else:
        conf_file = "compose.conf"

    try:
        compose_model(os.getcwd(),conf_file)  
    except KeyboardInterrupt,e:
        pass
    except Exception, e:
        print __doc__
        import traceback
        traceback.print_exc(file=sys.stderr)
        error("Error: %s" % e)

if __name__ == '__main__':
    _main()
