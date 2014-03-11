from twisted.internet import reactor
from twisted.trial.unittest import TestCase

from shortener.metrics import ShortenerCarbonClient


class TestShortenerMetrics(TestCase):
    def setUp(self):
        reactor.suggestThreadPoolSize(1)
        cfg = {
            'host_domain': 'http://wtxt.io',
            'account': 'test',
            'graphite_host': 'localhost',
            'graphite_port': 2001,
        }
        self.metrics = ShortenerCarbonClient(
            reactor=reactor,
            config=cfg
        )

    def test_metric_names(self):
        metric = self.metrics.get_metric_name('created.count')
        self.assertEqual(metric, 'test.wtxtio.created.count')
