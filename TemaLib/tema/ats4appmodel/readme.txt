ATS4AppModel2Lsts readme
########################

Introduction
+++++++++++++

ATS4AppModel2Lsts is a tool used to convert ATS4 AppModel 
(http://ats4appmodel.sourceforge.net/) XML-based models to TEMA lsts-based 
models that are executable with the TEMA test engine. The tool can be used 
both for creating a direct conversion or by instrumenting it to transform the 
ATS4 System model into a task switcher, allowing concurrent testing of 
application models.

Requirements
++++++++++++

- Tested with Python 2.5.2

Usage:
++++++

**./ats4appmodel2lsts.py [options] input_file**

The input file is the system model xml-file of the ATS4 model. The rest of the
ATS4 model is presumed to follow the regular ATS4 model directory hierarchy:

- Application models: system_model_name.xml.dat/apps/
- Test data: system_model_name.xml.dat/TestData/

Options
=======

--help, -h              show help message and exit

--output=OUTDIR, -o OUTDIR
                        Output path for the generated lsts model.
                        
--fullts                Generate a task switcher model from the ATS4 system
                        model including all states and transitions.
                        
--taskswitcher, -t      Generate simplified task switcher from the system model
                        that includes activations between application
                        models but omits other states and transitions.
                        
--generateSleep         Generate sleepts/wakets transitions for tagged states

--sleepByDefault        Handle states with no CanSleep/CanNotSleep tags as
                        CanSleeps

Direct conversion
===================
The direct conversion is a straightforward conversion from the ATS4 model. 
The resulting model does not contain any synchronizations between the 
different application models, thus inexplicit switches between the 
applications is not possible. This conversion is sufficient for models that 
contain only one application.

Task switcher conversion (-t and --fullts)
===========================================

When converting the model with task swicher generation options, the system 
model of ATS4 model is transformed into a task swither, that allows 
synchronizations between different application models. To make syncronizations
possible, application models should define which states are sleep states i.e. 
from which states the application can be set to background. Read more about 
sleep states below.

Taskswitcher conversion can be performed in two different ways: full task 
swicher conversion, or simplified task switcher conversion. The full 
taskswitcher conversion transfroms the system model to a task switcher, 
including all states and transitions it contains and adding activations 
between the applications. The simplified task swither searches all application
models from the system model, creates activations between them and converts 
the gate transition between the applications, but removes all other transition
or states that the system model may contain.

Task swicher uses the application model name as the application name when 
launching/setting applications to the foreground. If the process name is 
different than the application model name, the converter can be instructed to 
use another name by defining the process name in the description field of the 
application model in the following way: appname: "name"

Generating sleep states (--generateSleep, --sleepByDefault)
=============================================================

Sleep states are states where the application can be set to background. Valid 
sleep states are such where the state remains exactly same even if the 
application is returned to the foreground after a long period of time. For 
example states where some loading occurs are not good sleep states. Another 
example of an invalid sleep state is a state where a menu has been opened, and
setting the application to background automatically closes all open menus 
(Behaviour in S60 domain).

Determining which states can be considered as sleep states can't be done 
automatically. Therefore modeler can add specific labels to the ATS4 model to 
tell the converter which states are used as sleep states. These labels are 
"CanSleep" and "CanNotSleep" and they can be included anywhere in the state 
description field.

If a state has not been labeled with either "CanSleep" or "CanNotSleep", the 
default conversion considers it as "CanNotSleep". This behaviour can be 
changed by giving the "sleepByDefault" option, which tells the converter to 
handle state that does not have a label as "CanSleep".

Known issues
+++++++++++++

- LSTS.PY gives the following warning: set_actionnames did not receive "tau". 
  This is normal behaviour in LSTS module. Tau actions are not necessary for 
  the converted models, thus this warning does not have any effect on the 
  conversion result.

Contact information
++++++++++++++++++++

teams@cs.tut.fi
