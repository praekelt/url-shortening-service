from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from shortener.metrics import ShortenerCarbonClient


class TestShortenerMetrics(TestCase):
    timeout = 5

    def setUp(self):
        reactor.suggestThreadPoolSize(1)

        cfg = {
            'host_domain': 'http://wtxt.io',
            'account': 'test',
            'connection_string': "sqlite://",
            'graphite_host': 'localhost',
            'graphite_port': 2001,
        }
        self.metrics = ShortenerCarbonClient(reactor, cfg)

    @inlineCallbacks
    def test_class_mock(self):
        self.metrics.carbon_client.startService()
        yield self.metrics.publish_created_url_metrics()

    """
    TODO:  Once I get this set up stuff sorted, I will be using mock to
    mock out the actual call
    from mock import patch

    @inlineCallbacks
    @patch('txCarbonClient.CarbonClientService')
    def test_class_mock(self, MockClass):
    instance = MockClass.return_value
    instance.publish_metric.return_value = {}

    self.metrics.carbon_client.startService()
    yield self.metrics.publish_created_url_metrics()

    instance.publish_metric.assert_called_once_with('test.wtxtio.created.count', 1)
    """
