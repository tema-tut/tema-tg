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
Module for converting ATS4 AppModel (http://ats4appmodel.sourceforge.net/) XML
models to TEMA lsts models

Module provides Kendo2Lsts class that is used to handle the conversion, and 
the main function to use the converter.

"""

tool_description = """ATS4AppModel2Lsts is a tool used to convert ATS4 AppModel (http://ats4appmodel.sourceforge.net/) XML-based models to TEMA lsts-based models that are executable with the TEMA test engine. The tool can be used both for creating a direct conversion or by instrumenting it to transform the ATS4 System model into a task switcher, allowing concurrent testing of application models.

"""



from xml.dom import minidom
import os
import re
import sys
import shutil
import codecs
import optparse
import sys, traceback

import tema.lsts.lsts as lsts


import tema.ats4appmodel.lstsmodel as lstsmodel

from tema.ats4appmodel.kendomodel import *

    
class Kendo2Lsts:
    
    """
    ATS4 AppModel model converter class
    
    Uses kendomodel module to parse ATS4 AppModel xml-files and to create an 
    object hierarhy from them.
    Uses lstsmodel module to convert kendo object hierachy to lsts model and 
    to write the model to files.

    """

    def __init__(self):
        
        self.__kendoXMLParser = None
        self.__sysModelFile = None
    
    
    def readKendoModel(self, sysModelPath):
        
        self.__sysModelFile = sysModelPath
        self.__kendoXMLParser = KendoXMLParser(sysModelPath)
        return self.__kendoXMLParser.parseKendoModel()

        
         
    def printKendoModel(self):
        self.__kendoXMLParser.printKendoModel()
        
            
    
    def writeLstsModel(self, outputDir, create_taskswitcher, apps_only_ts, generateSleep, defaultSleep = True):
        
        output = outputDir
        if outputDir != "" and not outputDir.endswith(os.sep):
            output = output + os.sep
        
        lstsmodelname = output.split(os.sep)[-2]
        
        os.mkdir(output)
        os.mkdir(output + "rm" + os.sep)            
        
        model_names = []
        
        products = self.__kendoXMLParser.getProducts()
        system_model = products[0]
        
        if create_taskswitcher:
            print "Creating TaskSwitcher...",
            converter = lstsmodel.LstsModelCreator(products[0],products)
            model = converter.convertToTaskSwitcher(apps_only_ts, lstsmodelname +"-GateModel")
            
            model_names.append("TaskSwitcher-" + lstsmodelname)
            self.__writeLsts(model,"TaskSwitcher-" + lstsmodelname, output)
            
            gate_model = converter.createGateModel(products[0])
            model_names.append(lstsmodelname +"-GateModel")
            print "done"
            print "Writing TaskSwitcher...",
            self.__writeLsts(gate_model, lstsmodelname +"-GateModel", output) 
            print "done"
            #model_names.append(product.getName().replace(" ", "%20"))
            system_model = products.pop(0)
            
        for product in products:
            #TODO: if name not given use e.g. "product+id"
            #self.__writeLsts(product, output)
            print "Converting "+product.getName()+"...",
            converter = lstsmodel.LstsModelCreator(product, products)
            model = converter.convertProduct(create_taskswitcher, generateSleep, defaultSleep)
            print "done"
            
            modelName = lstsmodel.getModelName(product)
            print "Writing "+modelName+"...",
            self.__writeLsts(model, modelName, output)
            model_names.append(modelName)
            print "done"
        
        #Create variable models for flags
        print "Writing flag models...",
        self.__createFlagModels(output)
        

        for flag in self.__kendoXMLParser.getFlags():
            model_names.append("flagmodel_"+flag.getName())
        print "done"
        
        #Create empty -files for models ( no LaunchApps )
        #if not create_taskswitcher:
        #    for name in model_names:
        #        file = open(output + name + ".info", "w")
        #        file.close()
          
      
        #Create info files that contain the app_model name (Usually app-model name corresponds the launchApp name)             
        for state in system_model.getStates():
            if state.getType() == "APP_MODEL":
                appname = state.getName()
                matcher = re.search("[aA]ppname:\\s*\"(\\w+)\"",state.getDescription())
                if matcher:
                    appName = matcher.group(1)
            
                file = open(output + lstsmodel.getModelName(state.getLinkedProduct()) + ".info", "w")
                file.write("APPLICATION: " + appname + "\n")
                for sub in state.getLinkedProduct().getSubModels():
                    file = open(output + lstsmodel.getModelName(sub) + ".info", "w")
                    file.write("APPLICATION: " + appname + "\n")
                file.close()
        
        print "Generating Makefile...",
        self.__generateMakefile(output, model_names, lstsmodelname, create_taskswitcher)  
        print "done"  
        print "Creating testdata...",
        self.__createDataTables(output)
        print "done" 
        print "Creating coverage requirements based on the use cases...",
        self.__createCoverageRequirements(output, lstsmodelname)
        print "done"  
    

    def __writeLsts(self,lsts_model, model_name, outputDir):
        
        transitions = []
        
        states = lsts_model.getStates()
        actions = lsts_model.getActions()
        state_props = {}
        refinements = []

        for state in lsts_model.getStates():
            state_transitions = []
            for transition in state.getTransitions():
                #print states[0] == transition.getFromState()
                state_transitions.append((states.index(transition.getToState()), actions.index(transition.getAction())+1))
        
            transitions.append(state_transitions)
            
            for state_prop in state.getState_propositions():
                if state_prop.getName() in state_props:
                    state_props[state_prop.getName()].append(states.index(state))

                else:
                    state_props[state_prop.getName()] = []
                    state_props[state_prop.getName()].append(states.index(state))
                    if state_prop.getKeywords() != None and len(state_prop.getKeywords()) > 0:
                        if state_prop.getName() != "svStart":
                            refinements.append((state_prop.getName(), state_prop.getKeywords()))    
    
        action_names = []

        
        for action in actions:
            action_names.append(action.getName())
            if action.getRefinements() != None:
                refinements.append((action.getName(),action.getRefinements()))
        
        #self.__mergeStates(transitions, actions)            
        
        action_machine_file = open(outputDir + model_name + ".lsts", "w")
        ref_machine_file = codecs.open(outputDir + "rm" + os.sep + model_name + "-rm.lsts", "w", "iso-8859-1")
        
        w = lsts.writer(action_machine_file)
        w.set_actionnames(action_names)
        w.set_transitions(transitions)
        
        w.set_stateprops(state_props)     
        w.get_header().initial_states = states.index(lsts_model.getStart_state())
          
        w.write()
        
        #write refinement machines
        self.__writeRefinementMachine(refinements, ref_machine_file)
        

    
    
    def __mergeStates(self, transitionsList, actions):
        """
        Checks model for nondeterminism. If there is multiple transition with same action leaving a state,
        the target states of theses transitions are merged. This is currently needed to merge situations
        where multiple transitons are connected to a single InGate.
        
        NOTE: does not work in situations where there are transitions to the merging states outside from the state
        that is nondeterministic!
        
        TODO: Slow in big models ???
        
        
        
        removable_states = []
        
        for state_transitions in transitionsList:
            
            if state_transitions in removable_states: continue
            
            found = True
            
            while found:
                
                found = False
            
                for t1 in state_transitions:
                    
                    if found: break

                    for t2 in state_transitions:
                        
                        if t1 != t2 and t1[0] != t2[0] and t1[1] == t2[1]:
                            print "Indeterminism found! Merging states."
                            #state_transition.remove(t2)
                            mergingState = transitionsList[t2[0]]
                            mergeState = transitionsList[t1[0]]
                            mergeState.extend(mergingState)
                            removable_states.append(mergingState)
                            state_transitions.remove(t2)
                            found = True
                            break      
                        
        for rs in removable_states:
            #fix indexes of the transtitions 
            removed_index = transitionsList.index(rs)
            
            transitionsList.remove(rs)
            
            for state_transitions in transitionsList:
                temp_transitions = []
                for t in state_transitions:
                    if t[0] > removed_index:
                        temp = (t[0] - 1, t[1])
                        state_transitions[state_transitions.index(t)] = temp
                        
       """

       
    def __writeRefinementMachine(self, refinements, file):
        
        transitions = []
        actions = []
        
        #add central state
        transitions.append([])
        
        for ref in refinements:
            refName = ref[0]
            keywords = ref[1]
            

            #start aw/sv
            transitions.append([])
            actions.append("start_" + refName)
            transitions[0].append((len(transitions) - 1, len(actions)))
            
            prev_state_index = len(transitions) - 1
            
            #keywords
            for kw in keywords:
                
                if kw.strip() == "": continue

                matches = re.findall("\$(\w+)\$",kw)
                if matches != None and len(matches) > 0:
                    for match in matches:
                        #kw = lstsmodel.escape(kw.replace(match,"(OUT = " + match + ".name" + ")"))
                        kw = kw.replace(match,"(OUT = " + self.__removeIllegalChars(match).lower() + ")")
                if kw in actions:
                    kw_index = actions.index(kw) + 1
                else:
                    actions.append(kw)
                    kw_index = len(actions) 
                   
                transitions.append([])
                transitions[prev_state_index].append((len(transitions) - 1, kw_index))
                prev_state_index = len(transitions) - 1
            
            
            #end aw/sv
            actions.append("end_" + refName)
            transitions[prev_state_index].append((0, len(actions)))
            
        
        w = lsts.writer(file)
        w.set_actionnames(actions)
        w.set_transitions(transitions)

        w.write()
      
     
    def __createFlagModels(self, directory):
        
           
        for flag in self.__kendoXMLParser.getFlags():    
            actions = []
            transitions = []
            
            #Enabled state
            transitions.append([])
            enabled_index = 0            
            
            #Disabled state
            transitions.append([])
            disabled_index = 1
            
            enableAction = "ALLOW<Enabled" + flag.getName() + ">"
            disableAction = "ALLOW<Disabled" + flag.getName() + ">"
            
            toEnabledAction = "ALLOW<toEnabled" + flag.getName() + ">"
            toDisabledAction = "ALLOW<toDisabled" + flag.getName() + ">"
            
            actions.append(enableAction)
            enabled_action_index = 1
            
            actions.append(disableAction)
            disabled_action_index = 2
            
            actions.append(toDisabledAction)
            toDisabled_action_index = 3
            
            actions.append(toEnabledAction)
            toEnabled_action_index = 4
            
            transitions[enabled_index].append((disabled_index, toDisabled_action_index))
            transitions[enabled_index].append((enabled_index, enabled_action_index))
            transitions[enabled_index].append((enabled_index, toEnabled_action_index))
            
            transitions[disabled_index].append((disabled_index, toDisabled_action_index))
            transitions[disabled_index].append((disabled_index, disabled_action_index))
            transitions[disabled_index].append((enabled_index, toEnabled_action_index))
        
        
            file = open(directory + "flagmodel_" + flag.getName() + ".lsts", "w")
             
            w = lsts.writer(file)
            w.set_actionnames(actions)
            w.set_transitions(transitions)
            
            #Set right intial state based on the flag default state   
            if flag.getDefault_value() == False:
                w.get_header().initial_states = disabled_index
            else:
                w.get_header().initial_states = enabled_index
            
            w.write()  
            
            ref_machine_file = open(directory + "rm" + os.sep + "flagmodel_" + flag.getName() + "-rm.lsts", "w")
        
            #write refinement machines
            self.__writeRefinementMachine({}, ref_machine_file)
            

    def __createCoverageRequirements(self, directory, project_name):
    
    
        covRegNames = []
        covRegs = []
        
        ucModel = self.__kendoXMLParser.getUseCaseModel()

        file = open(directory + "usecase_coverage_requirements.txt", "w")

        if not ucModel:
            return
            
        for uc in ucModel.getUseCases():
          
            if uc.getDescription() != None and uc.getDescription() != "":
                description = ", description: " + uc.getDescription()
            else:
                description = ""
            
        
            file.write("Use case: " + uc.getName() + description + "\n\n")
            for path in uc.getPaths():
                actions = []
                
                
                for t in path.getTransitions():
                    modelName = t[0]
                    transitionId = t[1]
                    
                    product = None
                    transitionName = None
                    
                    for p in self.__kendoXMLParser.getProducts():
                        if p.getName() == modelName:
                            product = p
                            break
                    
                    if product:
                        for tt in product.getTransitions():
                            if tt.getId() == transitionId:
                                transitionName = tt.getEvent_id()
                                break
                        
                        if transitionName:
                        
                            actions.append(lstsmodel.getModelName(product) +":end_aw"+ transitionName)
                
                file.write("Path: " + path.getName() + ", " + path.getDescription() +"\n")
                covRegNames.append(uc.getName() + " : " + path.getName())
                
                covreg = ""
                for a in actions:
                    
                    if a == actions[0]:
                        covreg += "action " + a
                    else:
                        covreg += " THEN action " + a
    
                covRegs.append(covreg)
                file.write(covreg + "\n\n")
                    
            file.write("\n\n")    
            
        file.close()
        
        self.__createTestExecutionScript(covRegNames, covRegs, project_name, directory)


    def __createTestExecutionScript(self, covRegNames, covRegs, project_name, directory):

        """

        echo ""
        echo -n "Tallennetaanko loki ja makefile? [k/e] "
        read answer

        if [ "$answer" == "k" ]; then
            aikaleima=`date +"%F_%T" | sed 's/:/./g'`
            echo "Tallennan. Kirjoita kommentti"
                read kommentti
            cp -v /tmp/testengine-lastrun-demo.log logs/testrun-$aikaleima-$kommentti.log
            cp -v Makefile logs/testrun-$aikaleima.mak
            echo "Tallennettu."
        else
            echo "En tallentanut. Olisin tallentanut tiedostot:"
            echo "/tmp/testengine-lastrun.log"
            echo "Makefile"
        fi
        """

        
        file = open(directory + "run_test.sh", "w")
        
        script = "#!/bin/bash\n\n"
        
        script += """if [ "$1x" == "x" ]; then
            port=9095
        else
            port=$1
        fi
        """

        if covRegs and len(covRegs) > 0:
            i = 1
            for c in covRegs:
                script += "covRegs[" + str(i) + "]=\"" + c +"\"\n\n"
                i += 1
 
        script += "echo Choose coverage requirement:\n\n"
        
        i = 1
        if covRegs and len(covRegs) > 0:
            script += "echo Use cases:\n"

            for c in covRegNames:
                script += "echo \"" + str(i) + ": " + c +"\"\n"
                i += 1
            script += "echo \"\"\n"
       
        script += "echo " + str(i) + ": Define new coverage requirement\n" 
        script += "echo -n \"> \"\n"
        script += "read choice\n"
        
        
        script += "if [ $choice == "+str(i) +" ]\n"
        script += "then\n"
        script += "echo \"Enter coverage requirement: \"\n"
        script += "echo -n \"> \"\n"
        script += "read covReg\n"
        script += "else\n"
        script += "covReg=${covRegs[$choice]}\n"
        script += "fi\n"
        
        script += "echo executing coverage requirement: $covReg\n"
        
        script += "echo \"Choose heuristics:\"\n"
        script += "echo 1 : Random\n"
        script += "echo 2 : Greedy\n"
        script += "echo -n \"> \"\n"
        script += "read guidance\n"
        
        script += "if [ $guidance == 1 ]\n"
        script += "then\n"
        script += "guidance=\"randomguidance\"\n"
        
        
        script += "args=\"randomseed:$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]$[$RANDOM%10]\"\n"
        script += "echo $args\n"
        script += "elif [ $guidance == 2 ]\n"
        script += "then\n"
        script += "guidance=\"greedyguidance\"\n"
        script += "args=\"max_states:10000\"\n"
        script += "fi\n"
        
        script  += """tema testengine \\
            --model=parallellstsmodel:""" + project_name + """-rules.parallel \\
            --coveragereq="$covReg" \\
            --guidance="$guidance" \\
            --guidance-args="$args" \\
            --adapter-args="port:$port" \\
            --actionpp='' \\
            --actionpp-args='' \\
            --testdata='file:testdata.td' \\
            --logger='fdlogger' \\
            --logger-args='targetfile:/tmp/testengine-lastrun-""" + project_name + """.log,targetfd:stdout'"""
        
        file.write(script)
        
        
        
            

    def __generateMakefile(self, directory, model_names, project_name, generate_ts):
        
        file = open(directory + "Makefile", "w")
        file.write("all: " +project_name+"-rules.parallel\n")
        file.write("\n")
        file.write(project_name+"-rules.parallel:\n")
        file.write("\tmake -f Makefile-" + project_name + "\n")
        file.write("\n")
        file.write("clean:\n")
        file.write("\tmake -f Makefile-"+project_name+" clean")
        file.close()
        
        makefile_name = "Makefile-" + project_name
        file = open(directory + makefile_name, "w")
        
        models = ""
        for name in model_names:
            models = models + " " + name
        
        file.write("ACTIONMACHINELIST =")# +models)
        for m in model_names[0:-1]:
            file.write(m + " \\\n")
        file.write(model_names[-1])
        
        file.write("\n\n")

        file.write("DEVICE = rm")
        file.write("\n\n")
        file.write("RESULT = " + project_name + "-rules.parallel")
        file.write("\n\n")
        file.write("PYTHONLIBS=$(TEMA_ENGINE_HOME)/tema")
        file.write("\n\n")
        if generate_ts: file.write("#")
        file.write("TASKSWITCHERGEN=TaskSwitcher-"+project_name)
        file.write("\n")
        if generate_ts: file.write("#")
        file.write("TASKSWITCHERGENRM=TaskSwitcher-"+project_name+"-rm")
        file.write("\n\n")
        file.write("include $(TEMA_MODEL_TOOLS)/GNUmakefile.include")
        
        
    def __createDataTables(self, directory):
        """
        NOTE: Uses only the first data item. Rest dataitems are omitted.
        """
        
        
        file = codecs.open(directory + "testdata.td", "w","iso-8859-1")
        for dataEntity in self.__kendoXMLParser.getTestData():
            name = dataEntity.getLogicalName()
            if name == None or name == "":
                continue
            name = self.__removeIllegalChars(name).lower()
            

            
            if len(dataEntity.getItems()) > 0:
                file.write(name[1:len(name) - 1] + ":[")

                for dataItem in dataEntity.getItems():
                    
                    #Escape quotes
                    #TODO: re.escape ?
                    itemName = dataItem.getName()
                    itemName = re.sub("'","\\'",itemName)
                    itemName = re.sub("\"","\\\"",itemName)
                    #itemName = re.sub("\\","\\\\",itemName)
                    
                    file.write("'" + itemName + "'")
                    if dataItem != dataEntity.getItems()[-1]:
                        file.write(",")
                
                file.write("]\n")
            
            
            """
            try:
                dataItem = dataEntity.getItems()[0]
            except:
                continue
            
            itemName = dataItem.getName()
            itemName = re.sub("'","\\'",itemName)
            itemName = re.sub("\"","\\\"",itemName)
            file.write(name[1:len(name) - 1] + ":['" + itemName + "']\n")
            """
        file.close()
        
        """
        file = .open(directory + "testdata.td", "w","utf-8")
        
        logNames = []
        values = []
        
        for dataEntity in self.__kendoXMLParser.getTestData():
            name = dataEntity.getLogicalName()
            if name == None or name == "":
                continue
            logName = lstsmodel.escape(name[1:len(name) - 1])
            try:
                dataItem = dataEntity.getItems()[0]
            except:
                continue
            logNames.append(logName)
            values.append(dataItem.getName())
        
        file.write("Testdata(")
        for n in logNames:
            file.write(n)
            if n != lognames[-1]:
                file.write(",")
           
        file.write("):[(")
        for n in logNames:
            file.write(n)
            if n != lognames[-1]:
                file.write(",")
        file.write(")]\n")

        file.close()
        
        """
    
  
    
    
    
    def __removeIllegalChars(self,line):
    
        line = re.sub("\s|\W","_",line)
        if re.match("\d",line[0]):
            line = "_" + line
        return line
        
        
    
    
    

if __name__ == "__main__":
    
    #Parse command line arguments
    parser = optparse.OptionParser(usage="usage: %prog [options] input_file", description=tool_description)
    parser.add_option("-o", "--output", dest="outdir",
                      help="Output path for the generated lsts model.")
    parser.add_option("--fullts", dest="full_ts", default=False, action="store_true",
                      help="Generate a task switcher model from the ATS4 AppModel system model including all states and transitions..")
    parser.add_option("-t","--taskswitcher", dest="simple_ts", default=False, action="store_true",
                      help="Generate simplified task switcher from the system model that includes activations between application models but omits all other states and transitions..")
    parser.add_option("--generateSleep", dest="generateSleep", default = False, action="store_true", 
                      help="Generate sleepts/wakets transitions for tagged states")
    parser.add_option("--sleepByDefault", dest="defaultSleep", default = False, action="store_true", 
                      help="Handle states with no CanSleep/CanNotSleep tag as CanSleeps")
    #parser.add_option("-s", dest="sys_model",
    #                  help="ATS4 AppModel system model xml-file that is converted")
    #parser.add_option(")
    outputdir = None
    
    #Argument parsing...
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments")
        exit(1)
    else:
        if(options.outdir):
            if os.path.exists(options.outdir):
                print "Directory \""+ options.outdir +"\" exists. Overwrite? (y/n): ",
                while True:
                    answer = raw_input("").strip().lower()
                    if answer == 'y' or answer == 'yes':
                        try:
                            shutil.rmtree(options.outdir)
                            break
                        except:
                            print "Directory could not be rewritten"
                            exit(1)
                    elif answer == 'n' or answer == 'no':
                        exit(0)
                    else:
                        print "Please answer 'y' or 'n'."        
                        
            outputdir = options.outdir   
        else:
            print "Output directory must be defined."
            exit(1)
            
    if not os.path.exists(args[0]):
        print "Model: " + args[0] + " does not exist!"
        exit(1)
    
    sysmodefile = args[0]
    
    converter = Kendo2Lsts()
    #converter.parseKendoModel("voicerecorder_port.xml")
    print "Reading ATS4 AppModel model...",
    if not converter.readKendoModel(sysmodefile):
        exit(1)
    print "done"
    #converter.printKendoModel()
    converter.writeLstsModel(outputdir, options.full_ts or options.simple_ts, options.simple_ts,options.generateSleep, options.defaultSleep)
    print "Conversion complete."


