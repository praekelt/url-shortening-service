from urlparse import urlparse
from txCarbonClient import CarbonClientService
from twisted.internet.defer import inlineCallbacks


class ShortenerCarbonClient(object):
    def __init__(self, reactor, config):
        self.config = config
        self.domain = urlparse(config['host_domain']).netloc.replace('.', '')
        self.carbon_client = CarbonClientService(
            reactor,
            config['graphite_host'],
            config['graphite_port']
        )

    def get_metric_name(self, metric):
        return '%(account)s.%(domain)s.%(metric)s' % {
            'account': self.config['account'],
            'domain': self.domain,
            'metric': metric,
        }

    def publish_created_url_metrics(self):
        metric = self.get_metric_name('created.count')
        return self.carbon_client.publish_metric(metric, 1)

    def publish_expanded_url_metrics(self):
        metric = self.get_metric_name('expanded.count')
        return self.carbon_client.publish_metric(metric, 1)

    def publish_invalid_url_metrics(self):
        metric = self.get_metric_name('invalid.count')
        return self.carbon_client.publish_metric(metric, 1)
