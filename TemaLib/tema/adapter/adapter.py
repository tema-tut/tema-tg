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

This is an adapter to which the test engine forwards keywords.

Use:

1. No arguments to constructor:

   adapter=Adapter()


2. Setup necessary parameters

   adapter.setParameter(name,value)


3. Before starting communication through the adapter, make sure
   its connections are working:

   adapter.prepareForRun()


4. Work. Call:

   adapter.sendInput(keyword_action_name)

   it returns true/false depending on the status of the action.


4.5 If adapter has a method errorFound, it is called when the
    test engine detects an error.

    adapter.errorFound()

5. Stop.

   adapter.stop()


"""

class AdapterError(Exception): pass


class Adapter:

    def __init__(self):
        self._allowed_parameters=["logger"]
        self._params={}

    def log(self,*args): pass

    def setParameter(self,name,value):
        self._params[name]=value

    def sendInput(self,actionname):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError
    
