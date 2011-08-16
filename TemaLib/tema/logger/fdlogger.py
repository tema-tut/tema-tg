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
File (descriptor) logger reads the following parameters:

- targetfd (natural number or 'stdout' or 'stderr', default: 1)

  File descriptor to which the log entries are written. The default
  (1) equals to the standard output.

- targetfile (string, default: '')

  The name of the file to which the log entries are written. Specify
  either the number of file descriptor or the name of the file, but
  not both.

- targetgzipfile (string, default: '')

  The name of the file to which the log entries are written. File is
  written as gzip-compressed text file.

- exclude (string, default: '')

  The name of the class whose log entries will not be written
  out. You can give many exclude arguments.


Example:

  --logger-args='targetfile:log.txt,exclude:ParallelLstsModel,exclude:Adapter'
"""

import os
import sys
import time
import thread # only one log message can be written at a time
import gzip

class Logger:

    def __init__(self):
        self._exclude_class_list=[]
        self._targetfdlist=[]
        self._fileobjs=[]
        self._lock=thread.allocate_lock()

    def __del__(self):
        for f in self._fileobjs: f.close()

    def setParameter(self,name,value):
        if name=="exclude":
            self._exclude_class_list.append(value)
        elif name=="targetfd":
            if value=="stdout" or value==1: self._targetfdlist.append(1)
            elif value=="stderr" or value==2: self._targetfdlist.append(2)
            elif type(value)==int: self._targetfdlist.append(value)
            else: raise Exception("Allowed values for targetfd are 'stdout','stderr' and a number of a file descriptor")
        elif name=="targetfile":
            # Open file with no buffering to simulate behaviour, when writing
            # with os.write()
            self._fileobjs.append(open(value,"w",buffering=0))
        elif name=="targetgzipfile":
            self._fileobjs.append(gzip.GzipFile(filename=value,mode='wb',compresslevel=1))
        else:
            print __doc__
            raise Exception("Invalid parameter '%s' for fdlogger." % name)

    def prepareForRun(self):
        """Here we could open a file or socket, if necessary. In this
        logger there is no need to do anything special --- the given
        file descriptor is assumed to be open anyway."""
        # if not targets specified, use stdout (file descriptor 1)
        if self._targetfdlist==[] and self._fileobjs==[]: self._targetfdlist=[1]
        self.__class__.log=self.logmethod(self._targetfdlist,self._fileobjs,self._lock)
        self.log("FDLogger prepared for run %s"
                 % time.strftime("%Y-%m-%d-%H-%M-%S"))

    def listen(self,cls):
        """this method adds or replaces 'log' method of cls class by
        the log method of this class. In principle, here the name of
        the cls could be used to select fitting log method. For
        example, if we would like to omit all logging calls from class
        XXX, its log method could be replaced with devnulllog... """
        if not cls.__name__ in self._exclude_class_list:
            cls.log=self.logmethod(self._targetfdlist,self._fileobjs,self._lock)
        elif not hasattr(cls,'log'):
            # if cls does not have a log attribute, add a dummy one
            cls.log=lambda self,msg: None

    def logmethod(self,targetfdlist,fileobjlist,log_lock):
        def log(object,message):
            log_lock.acquire()
            t=time.time()
            timefrac=str(t-int(t))[2:5]
            timestr="%s.%s" % (time.strftime("%m%d%H%M%S",time.localtime(t)),
                               timefrac)
            classname=object.__class__.__name__
            logmsg="%s %s: %s\n" % (timestr,classname,message.replace('\\n','\n'))
            for targetfd in targetfdlist:
                os.write(targetfd,logmsg)
            for targetobj in fileobjlist:
                targetobj.write(logmsg)
            log_lock.release()
        return log
