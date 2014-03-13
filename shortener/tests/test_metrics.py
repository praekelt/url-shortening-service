from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from shortener.metrics import CarbonClientService
from shortener.tests.doubles import (
    DisconnectingStringTransport, StringTransportClientEndpoint)


class TestCarbonClientService(TestCase):
    timeout = 1

    def setUp(self):
        self.tr = DisconnectingStringTransport()
        endpoint = StringTransportClientEndpoint(reactor, self.tr)
        self.service = CarbonClientService(endpoint)

    @inlineCallbacks
    def test_start_stop(self):
        self.assertEqual(self.service.protocol_instance, None)
        self.service.startService()
        proto = yield self.service.connect_d
        self.assertEqual(self.service.protocol_instance, proto)
        self.assertNotEqual(proto, None)
        yield self.service.stopService()
        self.assertEqual(self.service.protocol_instance, None)

    @inlineCallbacks
    def test_send_metric(self):
        self.service.startService()
        yield self.service.connect_d
        self.assertEqual(self.tr.value(), "")
        self.service.publish_metric("foo", 3, 1394726782)
        self.assertEqual(self.tr.value(), "foo 3 1394726782\n")

    @inlineCallbacks
    def test_send_metric_while_stopped(self):
        self.assertEqual(self.tr.value(), "")
        self.service.publish_metric("foo", 3, 1394726782)
        self.assertEqual(self.tr.value(), "")
        self.service.startService()
        yield self.service.connect_d
        self.assertEqual(self.tr.value(), "foo 3 1394726782\n")
