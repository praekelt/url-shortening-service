import time
from urlparse import urlparse

from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet.endpoints import clientFromString

from shortener.reconnecting_client import ReconnectingClientService


class CarbonClientProtocol(Protocol):
    def publish_metric(self, name, value, timestamp):
        self.transport.write("%s %s %s\n" % (name, value, timestamp))


class CarbonClientFactory(ClientFactory):
    protocol = CarbonClientProtocol


class CarbonClientService(ReconnectingClientService):
    def __init__(self, endpoint):
        factory = CarbonClientFactory()
        ReconnectingClientService.__init__(self, endpoint, factory)
        self._metrics_queue = []
        self.protocol_instance = None
        self.connect_d = Deferred()

    def publish_metric(self, name, value, timestamp):
        self._metrics_queue.append((name, value, timestamp))
        self._process_queue()

    def _process_queue(self):
        if self.protocol_instance is not None:
            while self._metrics_queue:
                name, value, timestamp = self._metrics_queue.pop(0)
                self.protocol_instance.publish_metric(name, value, timestamp)

    def clientConnected(self, protocol):
        self.protocol_instance = protocol
        ReconnectingClientService.clientConnected(self, protocol)
        d = self.connect_d
        self.connect_d = Deferred()
        self._process_queue()
        d.callback(protocol)

    def clientConnectionLost(self, reason):
        self.protocol_instance = None
        ReconnectingClientService.clientConnectionLost(self, reason)


class ShortenerMetrics(object):
    def __init__(self, reactor, config):
        self.config = config
        self.domain = urlparse(config['host_domain']).netloc.replace('.', '')

        endpoint = clientFromString(reactor, config['graphite_endpoint'])
        self.carbon_client = CarbonClientService(endpoint)

    def get_metric_name(self, metric):
        return '%(account)s.%(domain)s.%(metric)s' % {
            'account': self.config['account'],
            'domain': self.domain,
            'metric': metric,
        }

    def publish_created_url_metrics(self):
        metric = self.get_metric_name('created.count')
        return self.carbon_client.publish_metric(metric, 1, time.time())

    def publish_expanded_url_metrics(self):
        metric = self.get_metric_name('expanded.count')
        return self.carbon_client.publish_metric(metric, 1, time.time())

    def publish_invalid_url_metrics(self):
        metric = self.get_metric_name('invalid.count')
        return self.carbon_client.publish_metric(metric, 1, time.time())
