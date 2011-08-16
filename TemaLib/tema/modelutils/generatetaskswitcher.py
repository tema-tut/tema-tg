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


# Author: Antti Kervinen, teams@cs.tut.fi, 2006

"""
Prints TaskSwitcher action machine or refinement machine to standard
output. 

Usage:

generatetaskswitcher <--amtgts Target>|<--am|--rm> <ActionMachine> [ActionMachine ...]

Examples:

Regular models
==============

Printing action machine:

generatetaskswitcher --am AliceTelephone AliceCalendar BobTelephone

Printing the corresponding refinement machine:

generatetaskswitcher --rm AliceTelephone AliceCalendar BobTelephone

Multitarget models
==================

Printing action machine for multitarget model:

generatetaskswitcher --amtgts Frank Camera%20-%20Main Camera%20-%20Startup > TaskSwitcher.lsts

Printing refinement machine for multitarget model:

generatetaskswitcher --rm TaskSwitcher Camera%20-%20Main Camera%20-%20Startup
"""

from __future__ import with_statement

import sys
import os

import tema.lsts.lsts as lsts

def find_application_name(fileobj):
    for line in fileobj:
        if "APPLICATION:" in line:
            return ' '.join(line.split()[1:]).strip()
    return None

def add_activation_transitions(taskswitcher, running_states_apps, amname, appname=""):
    """adds transitions needed for (de)activation of action machine
    called amname to the taskswitcher action machine."""

    if appname=="": appname=amname
    
    t=taskswitcher.get_transitions()
    a=taskswitcher.get_actionnames()
    p=taskswitcher.get_stateprops()

    # add new actions (if necessary):
    actnumCANWAKE=taskswitcher.get_header().action_cnt+1
    actnumWAKEWAKE=actnumCANWAKE+1
    actnumSLEEP=actnumCANWAKE+2
    actnumACTED=actnumCANWAKE+3
    a.append("WAKEtsCANWAKE<%s>" % amname)
    a.append("WAKEtsWAKE<%s>" % amname)
    a.append("SLEEPts<%s>" % amname)
    a.append("ACTIVATED<%s>" % amname)

    if appname: awactionname="awActivate<%s>" % appname
    else: awactionname="-- not an application"
    
    if not awactionname in a:
        actnumACTTE=actnumCANWAKE+4
        a.append(awactionname)
    else:
        actnumACTTE=a.index(awactionname)
        # we need to add 5 new actions anyway, therefore add
        # this dummy action (it won't be used anywhere)
        a.append("-- DONT_awActivate_ME<%s>" % amname)

    # add transitions
    newstate1=len(t)
    newstate2=newstate1+1
    newstate3=newstate1+2
    t[0].append((newstate1,actnumCANWAKE)) # CAN AM wake up?
    t.append([(newstate2,actnumACTTE)]) # if so, then activate AM
    t.append([(newstate3,actnumWAKEWAKE)]) # and then wake it up
    t.append([(0,actnumSLEEP)]) # allow AM to go to sleep

    p["%s running" % amname]=[newstate3]
    running_states_apps.append( (newstate3, amname) )

    # Allow the AM to activate any other AM
    # and allow any other AM to activate the AM
    i=3
    while i<=len(t)-3:

        # (i)-actnumACTED->(newstate3)
        t[i].append((newstate3,actnumACTED))

        # (newstate3)-actnumACT_{i/4}->(i)
        t[newstate3].append((i,(i/3)*5-1))

        i+=3

    p['SwitcherBase'] = [0]

    taskswitcher.set_actionnames(a)
    taskswitcher.set_transitions(t)
    taskswitcher.set_stateprops(p)

def extend_for_target_switching(taskswitcher, tgtname, running_states_apps):
    t=taskswitcher.get_transitions()
    a=taskswitcher.get_actionnames()

    # 1. Add actions, two for each action machine and two for initial state
    a.append("TARGET_DEACTIVATED")
    action_deact_tgt = len(a)-1
    old_initial_state = 0
    new_initial_state = len(t)
    t.append([])
    
    for state, app in running_states_apps:
        t[state].append((new_initial_state, action_deact_tgt))
        a.append("TARGET_ACTIVATED<%s>" % app)
        t[new_initial_state].append((state, len(a)-1))
        
    tgt_waking_state = len(t)
    t.append([])
    a.append("WAKEtgtsCANWAKE<%s>" % tgtname)
    t[new_initial_state].append((tgt_waking_state, len(a)-1))
    a.append("WAKEtgtsWAKE<%s>" % tgtname)
    t[tgt_waking_state].append((0, len(a)-1))
    a.append("SLEEPtgts<%s>" % tgtname)
    t[old_initial_state].append((new_initial_state, len(a)-1))

    taskswitcher.set_actionnames(a)
    taskswitcher.set_transitions(t)
    taskswitcher.get_header().initial_states = new_initial_state

def add_refinement_transitions(taskswitcherrm,amname,appname=""):

    if appname=="": appname=amname
    
    t=taskswitcherrm.get_transitions()
    a=taskswitcherrm.get_actionnames()

    # add new actions if necessary:
    if "start_awActivate<%s>" % appname in a:
        # awActivate is already refined here for this application
        return
    
    startaction=taskswitcherrm.get_header().action_cnt+1
    endaction=startaction+1
    kwaction=startaction+2
    a.append("start_awActivate<%s>" % appname)
    a.append("end_awActivate<%s>" % appname)
    a.append("kw_LaunchApp '%s'" % appname)
    taskswitcherrm.set_actionnames(a)

    # add states and transitions
    startstate=len(t)
    endstate=len(t)+1
    t[0].append( (startstate,startaction) )
    t.append([ (endstate,kwaction) ])
    t.append([ (0,endaction) ])
    taskswitcherrm.set_transitions(t)

def parse_args(argv):
    """ Parses command line arguments 
    
    :param argv: Argument vector
    :returns: Tuple (targetswitcher type, target name, actionmachinenames)
    :rtype: (str,str|None,[])
    """

    
    if len(argv)<3:
        print __doc__
        sys.exit(1)

    if "--help" in argv:
        print __doc__
        sys.exit(1)        

    machinetype = argv[1][2:]
    actionmachinenames = argv[2:]
    targetname = None
    addfunction = None

    if machinetype not in ["am","amtgts","rm"]:
        sys.stderr.write("Choose either action (--am or --amtgts for multitarget models) or refinement (--rm) machine.%s" % os.linesep)
        sys.exit(2)
    elif machinetype == "amtgts":
        targetname = actionmachinenames.pop(0)

    return (machinetype, targetname, actionmachinenames)

def main(working_directory, ts_type, targetname, action_machine_names, file_object ):


    running_states_apps = []
    taskswitcher=lsts.writer()

    # Create initial state and add "tau" action:
    taskswitcher.set_transitions([[]])
    taskswitcher.set_actionnames(["tau"])

    for am in action_machine_names:
        # To check the application name from the state proposition,
        # let's try to read the lsts file
        # try:
        #     amlsts=lsts.reader(open(am+".lsts"))
        #     amlsts.read()
        #     
        #     istate=amlsts.get_header().initial_states
        #     istateprops=lsts.props_by_states(amlsts)[istate]
        #     
        #     stateproplist=amlsts.get_stateprops().keys()
        #     stateproplist.sort()
        # except:
        #     istateprops=[]

        appname=""
        try:
            with open(os.path.join(working_directory,"%s.info" % am),'r') as am_file:
                appname=find_application_name( am_file )
        except IOError: 
            pass

        if not appname:
            pass
            #sys.stderr.write("generateTaskSwitcher: Warning: application name could not be found in '%s.info'%s" % (am,os.linesep))

        if ts_type in ["am","amtgts"]:
            add_activation_transitions(taskswitcher, running_states_apps, am, appname)
        elif ts_type == "rm":
            add_refinement_transitions(taskswitcher, am, appname)
        else:
            return False
            
    if ts_type == "amtgts" and targetname:
        extend_for_target_switching(taskswitcher, targetname, running_states_apps)

    taskswitcher.write(file_object)
    return True

if __name__ == "__main__":
    ts_type,target,am =  parse_args(sys.argv)
    main(os.getcwd(), ts_type, target, am, sys.stdout)
