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
SocketServerAdapter understands the following parameters:

- port (integer, default: 9090)

  the tcp/ip port which the server listens

- bindaddr (strings, default: '')

  IP address from which the connections are allowed. Set to localhost
  or 127.0.0.1 to allow connections from the local machine only.

- maxlen (integer, default: 5000)

  maximum length of message

- timeout (float = timeout in seconds,
          'None' = no timeout (blocked read),
          default = 'None')
"""


# tema libraries:
import tema.adapter.adapter as adapter
AdapterBase=adapter.Adapter
AdapterError=adapter.AdapterError

# python standard:
import socket

class Adapter(AdapterBase):

    """
    Protocol behaviour in methods:
    (always client talks first!)

    client          server

    prepareForRun():
    HELO       ->
               <-   ACK

    sendInput():
    GET        ->
               <-   ACK keyword
    PUT retval ->
               <-   ACK

    or

    BYE        ->
               <-   ACK
    which raises exception, client should
    not quit!

    errorFound():
    GET        ->
               <-   ERR
    client should repeat the request

    stop():
    GET        ->
               <-   BYE
    ACK        ->   server closes connection
    """

    def __init__(self):
        AdapterBase.__init__(self)
        self._allowed_parameters+=["port","bindaddr","maxlen","timeout"]
        self._params["port"]=9090
        self._params["bindaddr"]=''
        self._params["maxlen"]=5000
        self._params["timeout"]=None
        self._report_error=0

    def setParameter(self,name,value):
        if not name in self._allowed_parameters:
            print __doc__
            raise AdapterError("Illegal adapter parameter: '%s'." % name)
        
        if name=="timeout":
            try: self._params[name]=float(value)
            except ValueError:
                if value.lower()=="none": self._params[name]=None
                else: raise AdapterError("Invalid value for 'timeout' parameter. (float or None expected).")
        else:
            self._params[name]=value

    def prepareForRun(self):
        self.log("Using parameters %s" % self._params)
        self.log("Initializing socket.")
        try:
            self._socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind((self._params["bindaddr"],self._params["port"]))
            self._socket.listen(1)
        except Exception, e:
            raise AdapterError("Cannot listen socket '%s:%s'. Exception: %s"
                               % (self._params["bindaddr"],self._params["port"],e))

        self.log("Waiting for a connection from a client.")

        self._wait_for_connection()

        self._connection.settimeout(self._params["timeout"])

        msg=self._read_from_client()
        while not "HELO" in msg:
            self._write_to_client("NACK\n")
            msg=self._read_from_client()

        self._write_to_client("ACK\n")
        self.log("A client %s connected." % str(self._connection_from_host))

    def sendInput(self,action):
        # wait that the client requests keyword
        self.log("Waiting the client to request a keyword.")
        msg=self._read_from_client()
        while not "GET" in msg:
            self._write_to_client("NACK no keyword\n")
            self.log("Still waiting keyword request. Now got: '%s'" % msg.strip())
            msg=self._read_from_client()
        
        # keyword requested, send it.
        self.log("Sending [%s]" % action)
        self._write_to_client("ACK %s\n" % action)
        
        # wait for return value
        retval=""
        while not retval in ["true","false"]:
            self.log("Waiting the client to report the execution status.")
            msg=self._read_from_client()
            if msg[:3]=="GET": # re-send the keyword
                self.log("Client sent again request, not the report. Resending [%s]" % action)
                self._write_to_client("ACK %s\n" % action)
                continue
            try:
                putpart,retval=msg.strip().lower().split()
                if putpart!="put" or (putpart=="put" and not retval in ["true","false"]):
                    raise ValueError
            except ValueError: # could not split
                self.log("Still waiting execution status. Now got: '%s'" % msg.strip())
                self._write_to_client("NACK\n")
        self._write_to_client("ACK\n") # acknowledge PUT
        
        if retval=="true":
            self.log("The client reported successful execution of [%s]" % action)
            return True
        else:
            self.log("The client reported unsuccessful execution of [%s]" % action)
            return False

    def errorFound(self):
        # This is called instead of sendInput...
        self.log("Waiting the client to talk before talking about an error.")
        msg=self._read_from_client()
        # Drop the message, it should be resent by the client after
        # the error report.
        self.log("Informing the client about an error.")
        self._write_to_client("ERR\n")

    def stop(self):
        self.log("Shutting down, but the client should talk first.")
        msg=self._read_from_client()
        self.log("Saying BYE.")
        self._write_to_client("BYE\n")
        msg=self._read_from_client()
        while not (msg.rstrip() in ["", "ACK","BYE"]):
            self.log("Client should have said ACK but it said '%s'" % msg.rstrip())
            self.write_to_client("BYE\n")
            msg=self._read_from_client()
        self._quit_connection()

    def _quit_connection(self,with_ack=""):
        if with_ack:
            self._write_to_client(with_ack)
        self._connection.close()
        self._connection=None
        
    def _read_from_client(self):
        while 1:
            # read socket
            if not self._connection:
                raise AdapterError("cannot read, not connected")
            try:
                msg=self._connection.recv(self._params["maxlen"])
            except socket.error, e:
                self.log("socket error when reading: %s" % e)
                raise AdapterError("could not read from socket")

            # react to messages that are handled similarly in every state
            if msg[:3]=="BYE":
                self._quit_connection(with_ack="ACK\n")
                raise AdapterError("client said BYE")
            elif msg[:4]=="LOG ": # LOG must have a parameter, therefore "4"
                self.log("Client log: '%s'" % msg[4:].rstrip())
                self._write_to_client("ACK\n")
                continue
            else:
                return msg

    def _write_to_client(self,data):
        if not self._connection:
            raise AdapterError("cannot write, not connected")
        try:
            return self._connection.send(data)
        except socket.error, e:
            self.log("socket error when sending: %s" % e)
            raise AdapterError("could not write to socket")

    def _wait_for_connection(self):
        self._connection,self._connection_from_host=self._socket.accept()
