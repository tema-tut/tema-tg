#!/usr/bin/env python
#-*- coding: utf-8 -*-
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

import sys
import os
import time

launcher_path = os.path.realpath(sys.argv[0])
argv0 = sys.argv[0]

def executable_in_path(program):
    def is_executable(filepath):
        return os.path.exists(filepath) and os.access(filepath, os.X_OK)

    for path in os.environ["PATH"].split(os.pathsep):
        executable_file = os.path.join(path, program)
        if is_executable(executable_file):
            return executable_file
        
    return None

def strip_path( full_path, remove_this = "tema" ):
    (rest, last ) = os.path.split(full_path)
    while last and last != remove_this :
        # print rest, last, remove_this
        # sys.stdout.flush()
        # time.sleep(5)
        (rest, last ) = os.path.split(rest)
    return rest

tema_path = strip_path(launcher_path)
modelutils_path = os.path.join(strip_path(tema_path, "TemaLib"), "ModelUtils")
validation_path = os.path.join(strip_path(tema_path, "TemaLib"), "Validation")
mocksut_path =  os.path.join(tema_path,"MockSUT")
man_path = os.path.join(os.path.join(strip_path(tema_path, "TemaLib"), "Docs"),"man")

if tema_path not in sys.path:
    sys.path.reverse()
    sys.path.append(tema_path)
    sys.path.reverse()

command_set = dict()
command_set['testengine'] = "testengine.testengine"
command_set["mdm2svg"] = "eini.mdm2svg"

logtools = ["plotter","logreader","log2srt","sequencer"]

exec_commands = set([ "xsimulate", "simulate", "validate","analysator","runmodelpackage","help", "mocksut", "model2dot", "actionlist" ])
exec_commands.update(logtools)

modelutils_commands = set(["generatetaskswitcher","gt","rextendedrules","renamerules","composemodel","specialiser","generatetestconf"])
other_commands = set(["modelutils","engine_home","packagereader","ats4appmodel2lsts","variablemodelcreator","filterexpand","model2lsts","do_python","do_make"])
other_commands.update(modelutils_commands)

help_commands_exceptions = dict()

def print_usage(path,exec_commands,other_commands,command_set):
    print >> sys.stdout, "Usage:", os.path.basename(path), "<command>"
    print >> sys.stdout, ""
    print >> sys.stdout, "Available commands:"
    # Sort all commands and print them
    commands = []
    commands.extend(exec_commands)
    commands.extend(other_commands)
    commands.extend(command_set.keys())
    commands.sort()
    [ sys.stdout.write("  %s\n" % command ) for command in commands]

    print >> sys.stdout, ""
    print >> sys.stdout, "See 'tema help COMMAND' for more information on a specific command."
    print >> sys.stdout, "Note that all commands don't have help pages."

if len(sys.argv) < 2 :
    print_usage(argv0,exec_commands,other_commands,command_set)
    raise SystemExit(1)


sys.argv[0:1]=[]

## print >> sys.stderr, "__".join(sys.argv)

try:
    module= command_set[sys.argv[0]]
    if sys.argv[0] == "model2lsts":
        sys.argv[0] = "2lsts"
except KeyError:
    if sys.argv[0] in exec_commands :
        environment = os.environ
        base_command = sys.argv[0]
        exec_path = modelutils_path
        if sys.argv[0] == "simulate" or  sys.argv[0] == "xsimulate":
            exec_path = os.path.join(validation_path, "simulation")
            base_command = sys.argv[0] + ".py"

        if sys.argv[0] == "model2dot":
            exec_path = os.path.join(validation_path, "viewer")
            base_command = sys.argv[0] + ".py"


        if sys.argv[0] in ["runmodelpackage","actionlist"]:
            exec_path = modelutils_path
            base_command = sys.argv[0] + ".py"
        if sys.argv[0] == "mocksut":
            exec_path = mocksut_path
            base_command = sys.argv[0] + ".py"
        if sys.argv[0] == "help" :
            environment['MANPATH'] = man_path
            if len(sys.argv) == 1:
                print_usage(argv0,exec_commands,other_commands,command_set)
                raise SystemExit(1)
            
            if not sys.argv[1].startswith("tema."):
                command = "tema.%s" % (sys.argv[1])
            else:
                command = sys.argv[1]

            if command in help_commands_exceptions:
                sys.argv[1] = help_commands_exceptions[command]
            else:
                sys.argv[1] = command

            base_command = "man"
            for dir in os.environ.get('PATH', '').split(os.pathsep):
                candidate = os.path.join(dir,base_command)
                if os.path.isfile(candidate) and not os.path.isdir(candidate):
                    exec_path=dir
                    break
        if sys.argv[0] in logtools:
            exec_path = os.path.join(validation_path, "loghandling")
            base_command = sys.argv[0] + ".py"
        if sys.argv[0] == "validate" or sys.argv[0] == "analysator" :
            exec_path = os.path.join(validation_path, "analysis")
            base_command = sys.argv[0] + ".py"

        exec_path = os.path.join(exec_path, base_command)
        environment['PYTHONPATH'] = ":".join(sys.path)

        # print >> sys.stderr, exec_path
        try:
            os.execve( exec_path, sys.argv, environment )
        except Exception, e:
            print e
            print >> sys.stderr, exec_path
            raise SystemExit(1)

    elif sys.argv[0] in other_commands :
        if sys.argv[0] == "modelutils" :
            print modelutils_path
        elif sys.argv[0] == "engine_home" :
            print tema_path
        elif sys.argv[0] == "filterexpand" :
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            path = tema_path + "/tema/filter/filterexpand.py"
            args = sys.argv
            args[0] = path
            os.execve( path, args, environment )
        elif sys.argv[0] == "model2lsts" :
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            path = tema_path + "/tema/model/model2lsts.py"
            args = sys.argv
            args[0] = path
            os.execve( path, args, environment )
        elif sys.argv[0] in ["do_python"]:
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            path = sys.executable
            args = [path]
            os.execve(path,args,environment)
        elif sys.argv[0] in ["do_make"]:
            path = executable_in_path("gmake")
            if not path:
                path = executable_in_path("make")
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            environment['TEMA_MODEL_TOOLS'] = modelutils_path
            args = sys.argv
            args[0] = path
            os.execve(path,args,environment)
        elif sys.argv[0] in modelutils_commands:
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            path = tema_path + "/tema/modelutils/%s.py" % sys.argv[0]
            args = sys.argv
            args[0] = path
            os.execve( path, args, environment )

        elif sys.argv[0] == "packagereader" :
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            path = tema_path + "/tema/packagereader/packagereader.py"
            args = sys.argv
            args[0] = path
            os.execve( path, args, environment )
        elif sys.argv[0] == "variablemodelcreator" :
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            path = tema_path + "/tema/variablemodels/VariableModelCreator.py"
            args = sys.argv
            args[0] = path
            os.execve( path, args, environment )
        elif sys.argv[0] == "ats4appmodel2lsts"  :
            environment = os.environ
            environment['PYTHONPATH'] = ":".join(sys.path)
            path = tema_path + "/tema/ats4appmodel/ats4appmodel2lsts.py"
            args = sys.argv
            args[0] = path
            os.execve( path, args, environment )
    else:
        print >> sys.stderr, "Command", sys.argv[0], "not found"
        raise SystemExit(1)
    raise SystemExit(0)

__import__( module, globals(), locals(), [''])
