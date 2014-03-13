from twisted.internet.base import BaseConnector
from twisted.internet.endpoints import _WrappingFactory
from twisted.internet.error import ConnectionDone
from twisted.internet.interfaces import IStreamClientEndpoint
from twisted.python.failure import Failure
from twisted.test.proto_helpers import StringTransport
from zope.interface import implementer


class DisconnectingStringTransport(StringTransport):
    connector = None

    def loseConnection(self):
        if not self.connected:
            return

        self.connected = False
        reason = Failure(ConnectionDone("Bye."))
        self.protocol.connectionLost(reason)
        if self.connector is not None:
            self.connector.connectionLost(reason)


class StringTransportConnector(BaseConnector):

    def __init__(self, string_transport, factory, reactor):
        self._string_transport = string_transport
        BaseConnector.__init__(self, factory, None, reactor)

    def _makeTransport(self):
        self.reactor.callLater(0, self._connection_done)
        return self._string_transport

    def _connection_done(self):
        protocol = self.buildProtocol(None)
        self._string_transport.protocol = protocol
        self._string_transport.connector = self
        protocol.makeConnection(self._string_transport)

    def getDestination(self):
        return None


@implementer(IStreamClientEndpoint)
class StringTransportClientEndpoint(object):

    def __init__(self, reactor, string_transport):
        self._reactor = reactor
        self._string_transport = string_transport

    def connect(self, protocolFactory):
        wf = _WrappingFactory(protocolFactory)
        connector = StringTransportConnector(
            self._string_transport, wf, self._reactor)
        connector.connect()
        return wf._onConnection
