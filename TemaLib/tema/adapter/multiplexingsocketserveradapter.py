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
MultiplexingSocketServerAdapter understands the following parameters:

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

- clients (integer = number of clients to multiplex,
          default = 1)

- targettingkeyword (string = keyword used to switch target,
          default = 'SetTarget')
"""


# tema libraries:
import tema.adapter.socketserveradapter as adapter
AdapterBase = adapter.Adapter
AdapterError = adapter.AdapterError

# python standard:
import socket
import re
import copy


class Adapter(AdapterBase):

    """
    Protocol behaviour in methods:
    (always client talks first!)

    client1  client2         server

    prepareForRun():
    HELO              ->
                      <-     ACK
             HELO     ->
                      <-     ACK

    sendInput():
    GET               ->
             GET      ->
                      <-     ACK keyword
    PUT retval        ->
                      <-     ACK
    GET               ->
                      <-     kw_SetTarget client2
    PUT False         ->
             PUT True <-     kw_SetTarget client2


    or

    BYE               ->
                      <-     ACK
             GET      ->
                      <-     BYE
             ACK      ->     server closes connection
            
    which raises exception, client should
    not quit!

    errorFound():
    GET               ->
                      <-     ERR
    client should repeat the request

    stop():
    GET               ->
                      <-     BYE
    ACK               ->     server closes connection
             GET      ->     
                      <-     BYE
             ACK      ->     server closes connection    
            
    """

    def __init__(self):
        AdapterBase.__init__(self)
        self._allowed_parameters += ["clients","targettingkeyword"]
        self._params["clients"] = 1
        self._params["targettingkeyword"] = "SetTarget"
        self._connections = {}


    def setParameter(self, name, value):
        if not name in self._allowed_parameters:
            print __doc__
            raise AdapterError("Illegal adapter parameter: '%s'." % name)
        
        if name == "clients":
            adapter_error_message = "Invalid value for 'clients' parameter."
            try:
                value_tmp = int(value)
                if value_tmp >= 1:
                    self._params[name] = value_tmp
                else:
                    raise AdapterError("%s Value must be positive integer." 
                                       % adapter_error_message )
                
            except ValueError:
                raise AdapterError("%s (int expected)." % adapter_error_message)
        else:
            AdapterBase.setParameter(self, name, value)
            

    def prepareForRun(self):
        self.log("Using parameters %s" % self._params)

        self.log("Initializing socket.")
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind((self._params["bindaddr"], self._params["port"]))
            self._socket.listen(5)
        except Exception, e:
            raise AdapterError("Cannot listen socket '%s:%s'. Exception: %s"
                               % (self._params["bindaddr"],
                                  self._params["port"],e))

        try:
            while len(self._connections) < self._params["clients"]:

                self.log("Waiting for a connection from %i clients."
                         % ( self._params["clients"]
                             - len(self._connections)))

                self._wait_for_connection()
                self._connection.settimeout(self._params["timeout"])

                msg = self._read_from_client()

                while not msg.startswith("HELO"):
                    self._write_to_client("NACK\n")
                    msg = self._read_from_client()


                self.log("A client %s connected." \
                             % str(self._connection_from_host))
                self._connections[self._connection_from_host] = self._connection
#                self._connections.append(
#                    [self._connection,self._connection_from_host])

                self._write_to_client("ACK\n")
        except AdapterError,e:
            try:
                self.stop()
            except AdapterError,e2:
                pass
            raise e
                
        self.log("All clients connected.")

    def sendInput(self, action):

        m = re.match("[k|K]w_%s\s+(?P<target>.*)" % (self._params["targettingkeyword"]), action)
        # Handle targetting keyword as special case
        if m:
            target_name = m.group("target")
            self.log("Searching %s from targets" % target_name )

            clients = []
            clients.extend(self._connections.iteritems())
            for addr,conn in clients:
                self._connection = conn
                self._connection_from_host = addr
                try:
                    if AdapterBase.sendInput(self, action):
                        return True
                except AdapterError,e:
                    try:
                        self.stop()
                    except AdapterError,e2:
                        pass
                    raise e
                    
            else:
                self.log("Unknown target %s" % target_name)
                return False
        try:
            return AdapterBase.sendInput(self, action)
        except AdapterError,e:
            try:
                self.stop()
            except AdapterError,e2:
                pass
            raise e

    def stop(self):
        exception = None
        clients = []
        clients.extend(self._connections.iteritems())
        for addr,conn in clients:
            self._connection = conn
            self._connection_from_host = addr
            try:
                AdapterBase.stop(self)
            except AdapterError,e:
                if exception == None:
                    exception = e

        if exception != None:
            raise exception

    def errorFound(self):
        try:
            AdapterBase.errorFound(self)
        except AdapterError:
            self.stop()
            raise


    def _quit_connection(self,with_ack=""):
        old_addr = self._connection_from_host
        AdapterBase._quit_connection(self, with_ack)
        clients = []
        clients.extend(self._connections.iteritems())
        for addr,conn in clients:
            if addr == old_addr:
                self._connections.pop(addr)
                break
