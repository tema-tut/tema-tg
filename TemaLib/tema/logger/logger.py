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
This module implements the basis for logging system where many logger
objects may share the same targets and any logger object may have many
targets.

LoggerBase class shows the interface which every logger should
implement. When inherited, you should implement log,
_really_open_target and _really_close_target methods.

Every logger module should export Logger class inherited from
LoggerBase.

"""

_targetstr_refcount={}
_target_str2obj={}

def _attach_target(loggerobject,target):

    """Appends opened target object to the targets attribute of the
    logger object."""
    
    if _targetstr_refcount.get(target,0)>0:
        _targetstr_refcount[target]+=1
    else:
        targetobj=loggerobj._really_open_target(target)
        target_str2obj[target]=targetobj
        targetstr_refcount[target]=1
    loggerobj.targets.append(target_str2obj[target])

def _detatch_target(target):
    global target_logger_map, target_refcount

    if target_refcount[target]==1:
        target_logger_map[target]._really_close_target()

    target_refcount[target]-=1
    target_logger_map[target]

class LoggerBase:
    """Base class for multi-target logging."""
    def __init__(self):
        self.targets=[]
    
    def open(self,target):
        
        """Inform the target pool that this logger object will write
        to the target. If the target is not already open for writing,
        the target pool will call _really_open_target method of this
        object. The attach_target function will append the target to
        the self.targets list """
        
        _attach_target(self, target)

    def log(self,entry):

        """Write entry to open target. Most likely this includes row
        for t in self.targets: t.write(xxx) or t.send(xxx)."""
        
        raise NotImplementedError

    def close(self):
        """Inform the target pool that this logger will not be needing
        its targets anymore. Do not redefine this method --- if you
        still do, do not forget to call the original."""

        for t in self.targets:
            _detatch_target(self,t)

    def _really_close_target(self):        
        """This is a call-back from the target pool. If the last
        reference to the target has been closed, the target can be
        closed."""

        raise NotImplementedError

    def _really_open_target(self,target):
        """Open the target and return writable target object."""

        raise NotImplementedError
