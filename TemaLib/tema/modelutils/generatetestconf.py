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

"""
Test configuration generator

Usage: generateTestconf sourcedir testconfigurationfile targetdir

Generates a directory that includes models and data tables ready for a
test run. The files are originally located in sourcedir.
"""

import tema.eini.einiparser as einiparser
import shutil
import os
import stat
import sys
import tema.lsts.lsts as lsts

multipart_contents = r"""
[targets: type]
@TARGET@: rm

[targets: actionmachines[]]
@TARGET@: @ACTIONMACHINES@

[general: value]
type: single
result: rules.ext
taskswitchergen: TaskSwitcherGEN
taskswitchergenrm: TaskSwitcherGEN-rm
"""

multi_contents = r"""
[targets: conffile]
@TARGETS@

[general: value]
type: multi
result: combined-rules.ext
"""

GNUmakefile_contents = r"""

DEVICE=rm

RESULT=rules.ext

TASKSWITCHERGEN=TaskSwitcherGEN
TASKSWITCHERGENRM=TaskSwitcherGEN-rm

ACTIONMACHINELIST=$(filter-out $(TASKSWITCHERGEN), $(filter-out %-awgt, $(basename $(wildcard *.lsts))))

MAKEFILE_PATH:=$(shell python -c "import tema.modelutils;print tema.modelutils.MAKEFILE_PATH;")

include $(MAKEFILE_PATH)/GNUmakefile.include
"""

multitgt_GNUmakefile_contents = r"""
TARGETRULES=$(addsuffix /rules.ext, $(TARGETLIST))
RESULT=combined-rules.ext

PC_RULES_PATH:=$(shell python -c "import tema.modelutils;print tema.modelutils.PC_RULES_PATH;")
TEMA_ENGINE_HOME:=$(shell python -c "import os;import tema;print os.path.dirname(tema.__file__);")
MAKEFILE_PATH:=$(shell python -c "import tema.modelutils;print tema.modelutils.MAKEFILE_PATH;")

combined-rules.ext: $(TARGETRULES) multitarget-rules.ext
	# remove duplicate rows and rename Messaging:start_awX -> Frank/Messaging:start_awX
	cat $^ | python -c 'import sys; l=list(set(sys.stdin.readlines())); l.sort(); [sys.stdout.write(r) for r in l[::-1]]'                | sed 's:^(\([a-zA-Z0-9_]*\)/\([^/]*\),\(.*\)-> "\(\2\):(\1/\2,\3-> "\1/\4:g' > $@

multitarget-rules.ext: multitarget-rules.rext
	python $(TEMA_ENGINE_HOME)/modelutils/rextendedrules.py $< \
	| python $(TEMA_ENGINE_HOME)/modelutils/renamerules.py >$@


multitarget-rules.rext: $(TARGETRULES) TargetSwitcher-awgt.lsts TargetSwitcher-rm.lsts Synchronizer-awgt.lsts Synchronizer-rm.lsts.nolayout $(PC_RULES_PATH)/GenericPCRules-Multitarget
	$(RM) $@
	for target in $(TARGETLIST); do \
		egrep "^$$target/.+=\"" $$target/rules.ext >> $@; \
	done
	echo 'TargetSwitcher="TargetSwitcher-awgt.lsts"' >> $@
	echo 'TargetSwitcher-rm="TargetSwitcher-rm.lsts"' >> $@
	echo 'Synchronizer="Synchronizer-awgt.lsts"' >> $@
	echo 'Synchronizer-rm="Synchronizer-rm.lsts.nolayout"' >> $@
	cat $(PC_RULES_PATH)/GenericPCRules-Multitarget >> $@

Synchronizer.lsts:
	@echo "Synchronizer.lsts is missing, check generateTestconf."

Synchronizer-rm.lsts:
	@echo "Synchronizer-rm.lsts is missing, check generateTestconf."

%-awgt.lsts: %.lsts
	python $(TEMA_ENGINE_HOME)/modelutils/gt.py $< $@ \
		'P(s0,"sv$${.*}") -> P(s0,"sv$$=1.") T(s0,"start_sv$$=1.",s1) T(s1,"end_sv$$=1.",s0)' \
		'T(s0,"aw$${.*}",s1)T(s0,"~aw$$=1.",s2) -> T(s0,"start_aw$$=1.",s_new)T(s_new,"end_aw$$=1.",s1)T(s_new,"~end_aw$$=1.",s2)' \
		'T(s0,"aw$${.*}",s1)->T(s0,"start_aw$$=1.",s_new)T(s_new,"end_aw$$=1.",s1)' \
		'T(s0,"WAKEts",s1) -> T(s0,"WAKEtsCANWAKE",s_new) T(s_new,"WAKEtsWAKE",s1)'

%.lsts.iso: %.lsts
	iconv -f UTF-8 -t ISO-8859-1 $< > $@ || cat $< > $@

%.lsts.nolayout: %.lsts.iso
	python $(TEMA_ENGINE_HOME)/modelutils/gt.py $< $@ \
		'T(s0,"kw_return true",s1)T(s1,"end_aw$${.*}",s2)->T(s0,"end_aw$$=1.",s2)' \
		'T(s0,"kw_return false",s1)T(s1,"end_aw$${.*}",s2)->T(s0,"~end_aw$$=1.",s2)'

%/rules.ext:
	$(MAKE) -C $(subst /rules.ext,,$@)
	mv $@ $@.orig
	gawk -v TARGET=$(subst /rules.ext,,$@) '/^[0-9]+=/{print TARGET"/"gensub("=\"","=\""TARGET"/","1")}/") -> "/{s=gensub("\\(([0-9]+),\"","("TARGET"/\\1,\"","g"); print s}  !(/^[0-9]+=/ || /") -> "/){print $$0}' < $@.orig > $@.pass1
	gawk -v TARGET=$(subst /rules.ext,,$@) '/$(subst /rules.ext,,$@)\/[0-9]+=\"/{split($$0,a,"\""); newkey=gensub(".lsts.nolayout","","1",gensub("-awgt.lsts","","g",a[2]));keys[substr(a[1],1,length(a[1])-1)","]=newkey","; print newkey"=\""a[2]"\""}  /") -> "/{for (k in keys) gsub(k,keys[k]); print $$0} !(/$(subst /rules.ext,,$@)\// || /") -> "/){print $$0}' < $@.pass1 > $@


TargetSwitcher.lsts:
	python $(TEMA_ENGINE_HOME)/modelutils/generatetaskswitcher.py --am $(TARGETLIST) 		| sed -e 's/SLEEPts/SLEEPtgts/g' -e 's/WAKEts/WAKEtgts/g' > $@

TargetSwitcher-rm.lsts:
	python $(TEMA_ENGINE_HOME)/modelutils/generatetaskswitcher.py --rm $(TARGETLIST) 		| sed -e "s/LaunchApp '\([^']*\)'/SetTarget \$$(OUT=\1.id)\$$/g" > $@

clean:
	for tgt in $(TARGETLIST); do \
		$(MAKE) -C $$tgt clean; \
	done
	$(RM) combined-rules.ext TargetSwitcher.lsts TargetSwitcher-rm.lsts

include $(MAKEFILE_PATH)/GNUmakefile-utils.include
"""

def error(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(1)

def generate_synchronizer(iterable_target_names):
    """generate_synchronizer returns lsts_writer object"""
    outlsts = lsts.writer()

    actionnames = ["tau",
                   "WAKEtgt<Begin Synchronization>",
                   "REQALLtgt<Unprime Targets>",
                   "SLEEPtgt<End Synchronization: Success>",
                   "SLEEPtgt<End Synchronization: Failure>",
                   ]

    syncsucc_state = 2
    syncfailed_action = 4

    # (dest_state, action_number)
    transitions = [[(1,1)],[(3,2)],[(0,3)]]

    stateprops = {}

    for t in iterable_target_names:
        verifysucc_action = len(actionnames)
        actionnames.append("awVerify%s" % t)
        
        verifyfail_action = len(actionnames)
        actionnames.append("~awVerify%s" % t)
        
        reqprime_action = len(actionnames)
        actionnames.append("REQALLtgt<Prime %s>" % t)

        verifysucc_state  = len(transitions)+1
        verifyfail_state  = len(transitions)+2

        stateprops['successful verification of %s' % t] = [verifysucc_state]
        stateprops['failed verification of %s' % t] = [verifyfail_state]

        # from last failed verification state:
        transitions.append([(verifysucc_state, verifysucc_action),
                            (verifyfail_state, verifyfail_action)])

        # from verifysucc_state:
        transitions.append([(syncsucc_state, reqprime_action)])
        
    # from last failed verification state fail the whole thing:
    transitions.append([(0, syncfailed_action)])

    outlsts.set_actionnames(actionnames)
    outlsts.set_transitions(transitions)
    outlsts.set_stateprops(stateprops)
    return outlsts

def generate_synchronizer_rm(iterable_target_names):
    """returns lstswriter"""
    outlsts = lsts.writer()
    
    actionnames = ["tau",
                   "kw_return false",
                   "kw_return true"]
    
    return_false_action = 1
    return_true_action = 2

    transitions = [[]]

    for t in iterable_target_names:
        start_aw_action = len(actionnames)
        actionnames.append("start_awVerify%s" % t)
        end_aw_action = len(actionnames)
        actionnames.append("end_awVerify%s" % t)
        is_true_action = len(actionnames)
        actionnames.append("kw_IsTrue $(OUT = (syncTarget == %s.id))$" % t)
        is_not_true_action = len(actionnames)
        actionnames.append("~kw_IsTrue $(OUT = (syncTarget == %s.id))$" % t)

        # from initial state
        transitions[0].append((len(transitions), start_aw_action))
        transitions.append([(len(transitions)+1, is_true_action),
                            (len(transitions)+3, is_not_true_action)])
        transitions.append([(len(transitions)+1, return_true_action)])
        transitions.append([(0, end_aw_action)])
        transitions.append([(len(transitions)+1, return_false_action)])
        transitions.append([(0, end_aw_action)])

    outlsts.set_actionnames(actionnames)
    outlsts.set_transitions(transitions)
    return outlsts


def copy_files(filelist, targetdir, rename_attarget_to=None, allow_nonexistence=False):
    """filelist is a list of strings, targetdir a string"""
    for f in filelist:
        try: file(f)
        except IOError, e:
            if e.errno==21: continue # file is a directory
            elif e.errno==2 and allow_nonexistence: continue # file does not exist
            else: raise e
        try:
            if rename_attarget_to==None:
                shutil.copy(f, targetdir)
            else:
                new_contents = file(f).read().replace('@TARGET',rename_attarget_to)
                # this might be removable code...
                # new_contents = new_contents.replace('"SLEEPapp<','"SLEEPapp<%s: ' % (rename_attarget_to,))
                # new_contents = new_contents.replace('"WAKEapp<','"WAKEapp<%s: ' % (rename_attarget_to,))
                # new_contents = new_contents.replace('"REQ<','"REQ<%s: ' % (rename_attarget_to,))
                # new_contents = new_contents.replace('"REQALL<','"REQALL<%s: ' % (rename_attarget_to,))
                # new_contents = new_contents.replace('"ALLOW<','"ALLOW<%s: ' % (rename_attarget_to,))
                # new_contents = new_contents.replace('"SLEEPts"','"SLEEPts<%s>"' % (rename_attarget_to,))
                # new_contents = new_contents.replace('"WAKEts"','"WAKEts<%s>"' % (rename_attarget_to,))
                file(targetdir+"/"+f[f.rfind('/')+1:],"w").write(new_contents)
                    
        except IOError:
            error("Failed to copy file %s to directory %s" % (f,targetdir))

def mkdir(dirname):
    try:
        try:
            if not stat.S_ISDIR(os.lstat(dirname)[stat.ST_MODE]):
                raise Exception("Illegal file type")
        except OSError, e:
            if e.errno == 2: # file dirname does not exist
                os.mkdir(dirname)
            else:
                raise e
    except Exception, e:
        error("Failed to create directory %s, %s" % (dirname,e))

def create_file(filename, file_contents):
    try:
        file(filename,"w").write(file_contents)
    except Exception, e:
        error("Failed to create file %s, %s" % (filename,e))


def generatetestconf(sourcedir,testconfigurationfile,targetdir):

    targetdir = os.path.abspath(targetdir)
    result = einiparser.Parser().parse(file(testconfigurationfile))
    result['targets'], result['data']['datatables'], result['data']['localizationtables']

    assert('type' in result['targets'].fields())
    assert('actionmachines' in result['targets'].fields())
    curdir = os.getcwd()
    try:
        os.chdir(sourcedir)
        # create directory structure
        mkdir(targetdir)

        for target in result['targets']:
            mkdir(targetdir+"/"+target)
            mkdir(targetdir+"/"+target+"/rm")

        create_file(targetdir + "/targets.td", "targets: " + str([target for target in result['targets'].keys()]))

        # copy datatables
        copy_files(result['data']['datatables']['names'], targetdir)

        # copy localization tables
        copy_files(result['data']['localizationtables']['names'], targetdir)

        # copy action machines
        for target in result['targets']:
            copy_files(result['targets'][target]['actionmachines'],
                       targetdir+"/"+target,
                       rename_attarget_to = target)

            copy_files([f.rsplit('.', 1)[0] + '.info' for f in result['targets'][target]['actionmachines']],
                       targetdir+"/"+target)

            copy_files([result['targets'][target]['type']+"/"+f
                        for f in os.listdir(result['targets'][target]['type'])],
                       targetdir+"/"+target+"/rm",
                       rename_attarget_to = target)

            # Multipart conffile for model composing
            am = ",".join(result['targets'][target]['actionmachines'])
            create_file(os.path.join(targetdir,target,"compose.conf"),
                        multipart_contents.replace("@TARGET@",target).replace("@ACTIONMACHINES@",am))
            # GNUmakefile
            create_file(os.path.join(targetdir,target,"GNUmakefile"),
                        "TGTMAGIC=tgts %s\n%s" % (target,GNUmakefile_contents) )

        # Main conffile for model composing
        create_file(os.path.join(targetdir, "compose.conf" ),
                    multi_contents.replace("@TARGETS@","\n".join(["%s: compose.conf" % t for t in result['targets']])))


        create_file(os.path.join(targetdir, "GNUmakefile" ),
                    "TARGETLIST=" + " ".join([t for t in result['targets']]) \
                        + "\n" + multitgt_GNUmakefile_contents)


        # generate synchronizer-synchronizer and its refinement machine
        lstswriter = generate_synchronizer(result['targets'])
        lstswriter.write(file(targetdir+"/Synchronizer.lsts",'w'))
        lstswriter = generate_synchronizer_rm(result['targets'])
        lstswriter.write(file(targetdir+"/Synchronizer-rm.lsts",'w'))
    finally:
        os.chdir(curdir)

def main():
    try:
        generatetestconf(*sys.argv[1:])
    except Exception, e:
        print __doc__
        error("Error: %s" % e)

if __name__ == '__main__':
    main()
