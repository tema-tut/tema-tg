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
Commandline arguments (example):

model: REQUIRED
    test model specification (lstsmodel or parallellstsmodel)

coverage: REQUIRED
    coverage module
    Note: If not given, the proper coverage module is guessed based on the
          coveragereq string. (for backwards compatibility)

coveragereq: REQUIRED
    coverage requirement in a language accepted by the coverage module.

coveragereq-args:
    arguments for coverage module

initmodels:
    models for initialising a test run. These models are executed
    before the execution of the main test model is started.

testdata:
    datafiles that should be used in testing. $(expression)$ in the
    transition labels of models will be replaced using the data. Use 'nodata'
    to disable testdata

guidance & guidance-args:
    test selection module and its arguments

adapter & adapter-args:
    test adapter (socketserveradapter and its arguments)
    and its arguments

logger & logger-args:
    logger module and its arguments

actionpp & actionpp-args:
    action name postprocessor through which the actions are passed
    just before being sent to the adapter.

verify-states:
    1: always executes all the encountered state verifications
    0 (default): no special treatment to state verifications

testengine --model=parallellstsmodel:gallerycalendar.pcrules \\
           --coverage='clparser' \\
           --coveragereq='actions .*fullscreen.*' \\
           --initmodels='lstsmodel:close-apps.lsts,parallellstsmodel:initmodel.pcrules'\\
           --testdata='file:calendardata.td,file:gallerydata.td' \\
           --guidance=gameguidance \\
           --guidance-args='lookahead:15,randomseed:42' \\
           --adapter=socketserveradapter \\
           --adapter-args='port:9090' \\
           --logger='fdlogger'
           --logger-args='targetfd:stdout,exclude:ParallelLstsModel'
           --actionpp='localspp'
           --actionpp-args='file:S60v3localization.csv,lang:fi'
           --stop-after=1h30m
"""

import sys
import getopt
import random
import os
import time
import threading
import re

import signal
import traceback

# Save pid
run_pid = file("__engine_pid", "w")
print >> run_pid, os.getpid()
run_pid.close()


# Commandline arguments:
ARG_MODEL="model"
ARG_COVERAGE="coverage"
ARG_COVERAGE_REQ="coveragereq"
# A better name for this arg might be
# 'coverage-args' instead of 'coveragereq-args'
# but sticking by this for now for backwards compatibility.
ARG_COVERAGE_ARGS="coveragereq-args"
ARG_INITMODELS="initmodels"
ARG_DATA="testdata"
ARG_GUIDANCE="guidance"
ARG_GUIDANCE_ARGS="guidance-args"
ARG_CONF_FILE="config"
ARG_ADAPTER="adapter"
ARG_ADAPTER_ARGS="adapter-args"
ARG_LOGGER="logger"
ARG_LOGGER_ARGS="logger-args"
ARG_ACTIONPP="actionpp" # Actionname post-processor
ARG_ACTIONPP_ARGS="actionpp-args"
ARG_STOP_AFTER="stop-after"
ARG_VERIFY_STATES="verify-states"

CMDLINE_ARGUMENTS=[ "%s" % a
                    for a in (ARG_MODEL,
                              ARG_DATA,
                              ARG_COVERAGE,
                              ARG_COVERAGE_ARGS,
                              ARG_COVERAGE_REQ,
                              ARG_INITMODELS,
                              ARG_CONF_FILE,
                              ARG_GUIDANCE,
                              ARG_GUIDANCE_ARGS,
                              ARG_ADAPTER,
                              ARG_ADAPTER_ARGS,
                              ARG_LOGGER,
                              ARG_LOGGER_ARGS,
                              ARG_ACTIONPP,
                              ARG_ACTIONPP_ARGS,
                              ARG_STOP_AFTER,
                              ARG_VERIFY_STATES) ]

# arguments without default values are required in the command line

CMDLINE_DEFAULTS={ ARG_COVERAGE: "",
                   ARG_COVERAGE_ARGS: "",
                   ARG_CONF_FILE: "",
                   ARG_DATA: "",
                   ARG_INITMODELS: "",
                   ARG_GUIDANCE: "gameguidance",
                   ARG_GUIDANCE_ARGS: "",
                   ARG_ADAPTER: "socketserveradapter",
                   ARG_ADAPTER_ARGS: "port:9090",
                   ARG_LOGGER: "fdlogger",
                   ARG_LOGGER_ARGS: "targetfd:stdout",
                   ARG_ACTIONPP: "",
                   ARG_ACTIONPP_ARGS: "",
                   ARG_STOP_AFTER: "",
                   ARG_VERIFY_STATES: "0"
                   }


def error(errmsg,errcode=1):
    sys.stderr.write("%s: ERROR: %s\n" % (sys.argv[0],errmsg))
    sys.exit(errcode)

def print_traceback(fileobject=sys.stderr):
    # At the moment print only same traceback that we would get, if we 
    # hadn't caught the exception.
    type,value,traceb = sys.exc_info()
    traceback.print_exception(type,value,traceb,file=fileobject)

class CallGuidance:
    def __init__(self, guidance_object, current_state):
        self.__object = guidance_object
        self.__from_here = current_state
        self.__ev = threading.Event()
        self.__ev.clear()
        self.__rval = []
        self.__ok = False
    def __call__(self):
        try:
            self.__rval[:] = [ self.__object.suggestAction(self.__from_here) ]
            self.__ok = True
        finally:
            self.__ev.set()
    def wait_value(self, limit):
        wait_time = None
        if limit > 0 :
            wait_time = limit - time.time()
        self.__ev.wait( wait_time )
        if self.__ok :
            return self.__rval[0]
        else:
            raise SystemExit



class TestEngine:
    """This one-method class is a class instead of a pure function
    because we want to use the same logging mechanism as in other
    classes: log method is plugged in by the Logger.listen method."""

    def set_stop_time(self, timestr):
        # Determine time zone offset to UTC
        if time.localtime().tm_isdst:
            timezone = -time.altzone / 60 / 60.0
        else:
            timezone = -time.timezone / 60 / 60.0

        if timezone >= 0:
            timeoffset = "+" + str(timezone)
        else:
            timeoffset = str(timezone)
        
        self.log("Local time zone UTC%s" % timeoffset )
        
        if timestr!="":
            if 'h' in timestr: hours, timestr = timestr.split('h')
            else: hours = 0
            if 'm' in timestr: mins, timestr = timestr.split('m')
            else: mins = 0
            if 's' in timestr: secs, timestr = timestr.split('s')
            else: secs = 0
            try: 
                if timestr: raise Exception("Extra characters after seconds.")
                hours, mins, secs = int(hours), int(mins), int(secs)
            except Exception, e:
                self.log("Syntax error in stop time, use format 1h30m50s")
                raise Exception("Invalid time format.")
            self._stop_time = time.time() + secs + 60*mins + 3600*hours
            self.log("Test run will be stopped at %s" % 
                     time.strftime("%F %T",time.localtime(self._stop_time)))
        else:
            self._stop_time = 0.0

    def run_test(self,testmodel,current_state,covreq,testdata,guidance,adapter,appchain,verifier=None):

        # FIXME: Should this be a class method?
        def handler(signum,frame):
            raise Exception("Signal %i received" % signum )
        # Signals we are catching
        signal.signal(signal.SIGTERM,handler)

        stepcounter=0

        # clean model cache after every 10000 executions.
        # some guidances may clean up the cache themselves
        # but even if they don't, make sure it's cleared once in a while
        # to avoid consuming too much memory.
        cacheClearanceInterval = 10000
        executionsSinceCacheClearange = 0

        self.log("Testing starts from state %s" % current_state)

        while (self._stop_time == 0.0 or time.time() < self._stop_time) and covreq.getPercentage()<1.0 and len(current_state.getOutTransitions())>0:

            stepcounter+=1

            # 1. Choose action to be executed

            # If verifier is set and it gives an action, we'll execute that.
            # Otherwise, guidance chooses the action to be executed.

            if verifier: verifying_action = verifier.getAction(current_state)
            else:        verifying_action = None

            if verifying_action is None:
                if guidance.isThreadable():
                    guid = CallGuidance(guidance, current_state)
                    t = threading.Thread(target=guid)
                    t.setDaemon(True)
                    t.start()
                    try:
                        suggested_action = guid.wait_value(self._stop_time)
                    except SystemExit:
                        break
                else:
                    suggested_action=guidance.suggestAction(current_state)
            else:
                suggested_action = verifying_action

            
            self.log("Step     : %5i Covered: %7.4f %% Next: %s" % \
                     (stepcounter,covreq.getPercentage()*100.0,suggested_action))

                     
            # 2. Evaluate testdata, communicate with the SUT, if necessary
            if suggested_action.isKeyword():
                # Keywords cause communication
                try:
                    # force keyword to be positive (without '~')
                    # before sending
                    if suggested_action.isNegative():
                        sent_action_name=suggested_action.negate()
                    else:
                        sent_action_name=suggested_action.toString()
                    #adapter._set_current_state_UGLY_HACK(current_state)
                    result=adapter.sendInput(
                        appchain.process(
                        testdata.processAction(sent_action_name)))
                except AdapterError,e:
                    self.log("Adapter error, cannot continue: %s" % e)
                    return "Adapter error: %s" % e
                
                if suggested_action.isNegative():
                    if result==True:
                        executed_action_name=suggested_action.negate()
                    else:
                        executed_action_name=suggested_action.toString()
                else:
                    if result==True:
                        executed_action_name=suggested_action.toString()
                    else:
                        executed_action_name=suggested_action.negate()
            else:
                # Action is not a keyword => no communication
                executed_action_name=suggested_action.toString()
                testdata.processAction(executed_action_name)


            # 3. Check that we can execute executed_action_name also in
            #    the model

            possible_transitions=[ t for t in current_state.getOutTransitions() \
                                   if t.getAction().toString()==executed_action_name ]
            # TBD: the line above seems/seemed to not find any actions sometimes
            # (when there's only the ~ version of the action possible?) ??
            # would this line be better??
            #possible_transitions=[ t for t in current_state.getOutTransitions() \
            #                       if t.getAction().toString()==str(suggested_action)]

            if possible_transitions==[]:
                # Model can not execute the required action =>
                # *** error found ***
                self.log("Error found: cannot execute '%s' in the model" % executed_action_name)
                try:
                    if hasattr(adapter,"errorFound"): adapter.errorFound()
                except AdapterError,e:
                    self.log("Adapter error when it was being informed about an error: %s" % e)

                self.log("Shutting down the adapter")
                try:
                    adapter.stop()
                except AdapterError,e:
                    self.log("Adapter error when tried to quit the connection: %s" % e)
                self.log("Verdict: FAIL")

                return "Error found: cannot execute '%s' in model state %s." % \
                      (executed_action_name,current_state)

            # 4. Execute the transition (if many, print warning on nondeterminism)
            chosen_transition=random.choice(possible_transitions) 
            if len(possible_transitions)>1:
                print "Non determinism:",[str(t) for t in possible_transitions]

            self.log("Executing: %s" % chosen_transition.getAction())
            self.log("New state: %s" % chosen_transition.getDestState())

            # print stateprops only for every start_aw because there a so many
            # of them and printing them in every point would bloat the log...
            if "start_aw" in str(chosen_transition):
                self.log("(Non-SleepState) StateProps: %s"
                    % " ".join(['"%s"'%s for s in
                        chosen_transition.getDestState().getStateProps()
                        if "SleepState" not in str(s)] ))

            guidance.markExecuted(chosen_transition)

            if verifier: verifier.markExecuted(chosen_transition)

            current_state=chosen_transition.getDestState()

            executionsSinceCacheClearange += 1
            if executionsSinceCacheClearange >= cacheClearanceInterval:
                testmodel.clearCache()
                executionsSinceCacheClearange = 0

            # 5. Then loop.

        # Out of loop...
        result_comment="____ Undefined ____"
        if (self._stop_time > 0.0 and time.time() > self._stop_time):
            self.log("Time to stop")
            self.log("Verdict: PASS")
            result_comment = "Time to stop."
        elif covreq.getPercentage()<1.0:
            self.log("Cannot continue from state %s, no outgoing transitions." % current_state)
            # self.log("Verdict: INCONCLUSIVE")
            result_comment =  "Deadlock reached in the test model."
        else:
            self.log("Required coverage acquired")
            self.log("Verdict: PASS")
            result_comment =  "Coverage requirement fulfilled."
        self.log("Shutting down the adapter")
        try:
            adapter.stop()
        except AdapterError,e:
            self.log("Adapter error when tried to quit the connection: %s" % e)
        return result_comment


class ArgumentError (Exception): pass

def parse_arguments(arglist):
    """returns argument-value pairs in dictionary"""
    try:
        optlist,rest=getopt.getopt(arglist,
                            [],
                            [ "%s=" % a for a in CMDLINE_ARGUMENTS ])
        if rest!=[]: raise ArgumentError("Unable to parse argument '%s'" % str(rest[0]))
        retval={}
        retval.update(CMDLINE_DEFAULTS)
        for k,v in optlist:
            retval[k[2:]]=v # remove '--' in front of the option name

        # require that every argument has a value (either default or explicit)
        for k in CMDLINE_ARGUMENTS:
            if not k in retval: raise ArgumentError("Missing argument: --%s" % k)
        
        return retval
    except getopt.GetoptError,e:
        raise ArgumentError(e)


def import_tema_modules(options):
    # the following classes will be imported from libraries:
    global InitEngine, Model, Guidance, CoverageRequirement, TestData, Adapter, AdapterError, Logger

    # LastNameValue object will receive test model type and file name
    class LastNameValue:
        def setParameter(self,name,value): self.name,self.value=name,value

    try:
        from tema.initengine.initengine import InitEngine

        if options[ARG_COVERAGE]:
            # if coverage param given, import that coverage module
            coveragemodule=__import__("tema.coverage."+ options[ARG_COVERAGE],
                                       globals(),locals(),[''])
            CoverageRequirement = coveragemodule.requirement
        elif options[ARG_COVERAGE_REQ]:
            # otherwise, guess the coverage module from the coverage req string
            reqStr = options[ARG_COVERAGE_REQ].strip()
            if reqStr.startswith("action"):
                from tema.coverage.clparser import requirement\
                        as CoverageRequirement
            elif reqStr.startswith("findnew"):
                from tema.coverage.findnewcoverage import requirement\
                        as CoverageRequirement
            else:
                from tema.coverage.altercoverage import requirement\
                        as CoverageRequirement
        else:
            # Neither coverage or coverage-req given.
            # Use dummy coverage module which shows always zero percentage.
            from tema.coverage.dummycoverage import CoverageRequirement


        if options[ARG_DATA] == "nodata" :
            from tema.data.nodata import TestData
        else:
            from tema.data.testdata import TestData

        # imported model module depends on the parameters...
        nv=LastNameValue()
        set_parameters(nv,options[ARG_MODEL])
        # now nv.name = model module name, nv.value = model file name
        modelmodule=__import__("tema.model."+nv.name,globals(),locals(),[''])
        Model=modelmodule.Model
        Model.ARG_source_file=nv.value # Model will be loaded from source_file

        # imported guidance depends on the parameters...
        guidancemodule=__import__("tema.guidance."+options[ARG_GUIDANCE],globals(),locals(),[''])
        Guidance=guidancemodule.Guidance

        # imported adapter depends on the parameters...
        adaptermodule=__import__("tema.adapter."+options[ARG_ADAPTER],globals(),locals(),[''])
        Adapter=adaptermodule.Adapter
        AdapterError=adaptermodule.AdapterError

        # imported logger depends on the parameters...
        loggermodule=__import__("tema.logger."+options[ARG_LOGGER],globals(),locals(),[''])
        Logger=loggermodule.Logger

    except ImportError, e:
        error("import failed: '%s'. Is TemaLib in PYTHONPATH?" % e)
    except Exception, e:
        error("import failed: '%s'." % e)


def set_parameters(object,argument_string):
    """Parse argument string and call setParameter-method of the
    object accordingly. For example argument string
    'port:9090,yellowflag,logger:adapterlog' implies calls
    setParameter('port',9090), setParameter('yellowflag',None),
    setParameter('logger',adapterlog_object)."""
    # TODO: implement special object-type parameters (not needed so far)
    for argpair in argument_string.split(","):
        if not argpair: continue
        if ":" in argpair:
            name,value=argpair.split(":",1)
        else:
            name,value=argpair,None
        try: object.setParameter(name,int(value))
        except Exception,e:
            if not (isinstance(e,TypeError) or isinstance(e,ValueError)): raise e
            try: object.setParameter(name,float(value))
            except Exception,e: 
                if not (isinstance(e,TypeError) or isinstance(e,ValueError)): raise e
                object.setParameter(name,value)

### main
def main():
    try: options=parse_arguments(sys.argv[1:])
    except ArgumentError, e:
        print __doc__
        print sys.argv
        error(e)

    import_tema_modules(options)

    # try to optimize
    try:
        import psyco
        psyco.full()
    except:
        print "Sadly, there is no Psyco optimization available."

    # setup logger
    try:
        logger=Logger()
        try:
            set_parameters(logger,options[ARG_LOGGER_ARGS])
        except Exception, e: error("setting up logger arguments failed: '%s'" % e)
        logger.prepareForRun()

        # logger seems to be fine.  Now assign it to every other class
        logger.listen(InitEngine)
        logger.listen(Model)
        logger.listen(Guidance)
        logger.listen(Adapter)
        logger.listen(TestData)
        logger.listen(CoverageRequirement)
        logger.listen(TestEngine)

        # if logging of some classes was excluded, add dummy log methods:
        for cls in [Model, Guidance, Adapter, CoverageRequirement, TestEngine]:
            if not hasattr(cls,'log'):cls.log = lambda self,message: None
        
    except Exception,e: error("setting up logger failed: '%s'" % e)


    # Initialize test run
    try:
        initengine=InitEngine()
        set_parameters(initengine,options[ARG_INITMODELS])
    except Exception, e: error("setting up initmodel failed: '%s'" % e)

    # setup test model
    try:
        model=Model()
        model.loadFromFile( file(Model.ARG_source_file) )
        initial_state=model.getInitialState()
    except Exception, e: error("setting up test model failed: '%s'" % e)


    # setup coverage
    try:
        covreq=CoverageRequirement( options[ARG_COVERAGE_REQ], model=model )
    except Exception, e: error("reading coverage requirement failed: '%s'" % e)
    
    # set covreq arguments (if given)
    if options[ARG_COVERAGE_ARGS]:
        try:
            set_parameters(covreq,options[ARG_COVERAGE_ARGS])
        except Exception, e: error("setting covreq arguments failed: '%s'" % e)

    # Output all the action words to the log for debug, benchmarking
    # etc. purposes.
    model.log("Action words: %s" %
              (" ".join(model.matchedActions([re.compile(".*:end_aw.*")]))))

    # setup test data
    try:
        testdata=TestData()
        set_parameters(testdata,options[ARG_DATA])
        testdata.prepareForRun()
    except Exception, e: error("setting up test data failed: '%s'" % e)

    # setup guidance
    try:
        guidance=Guidance()
        try:
            set_parameters(guidance,options[ARG_GUIDANCE_ARGS])
        except Exception, e: error("setting up guidance arguments failed: '%s'" % e)
        guidance.setTestModel(model)
        guidance.addRequirement(covreq)
        guidance.prepareForRun()
    except Exception, e:
        if not isinstance(e,SystemExit):
            error("setting up guidance failed: '%s'" % e)
        else: raise e

    # state verifier
    if int(options[ARG_VERIFY_STATES]):
        from tema.guidance.stateverifier import StateVerifier
        verifier = StateVerifier()
    else:
        verifier = None

    # import action postprocessors
    import tema.actionpp.actionpp
    appchain=tema.actionpp.actionpp.ActionPPChain()
    if options[ARG_ACTIONPP]!="":
        appmodule=__import__("tema.actionpp."+options[ARG_ACTIONPP],globals(),locals(),[''])
        logger.listen(appmodule.ActionPP)
        app=appmodule.ActionPP()
        set_parameters(app,options[ARG_ACTIONPP_ARGS])
        appchain.append(app)

    # setup adapter
    try:
        adapter=Adapter()
        try:
            set_parameters(adapter,options[ARG_ADAPTER_ARGS])
        except Exception, e: error("setting up adapter arguments failed: '%s'" % e)
        adapter.prepareForRun()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception, e:
        if not isinstance(e,SystemExit):
            error("setting up adapter failed: '%s'" % e)
        else: raise e

    try:
        initengine.run_init(adapter, testdata, appchain)
    except Exception, e: error("test run initialization failed: '%s'" % e)
    
    # Run!
    te=TestEngine()
    te.set_stop_time(options[ARG_STOP_AFTER])

    result = ""
    # Catch exceptions so that logger would close the filehandles and write
    # buffers to disk.
    try:
        result=te.run_test(model,initial_state,covreq,testdata,guidance,adapter,appchain,verifier)
    # We don't want stack trace for normal exit
    except SystemExit,e:
        raise
    # In 2.4, Exception is a base class for all exceptions, but starting with 2.5, BaseException is a base class.
    # KeyboardInterrupt is inherited from BaseException in 2.5, but in 2.4 from Exception.
    except KeyboardInterrupt,e:
#        print_traceback()
        sys.exit(1)
    except Exception,e:
#        print e
        print_traceback()
        sys.exit(1)

    print "Test ended:",result
try:
    main()
except Exception,e:
    print e
    sys.exit(1)
