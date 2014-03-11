from txCarbonClient import CarbonClientService


class ShortenerCarbonClient(object):
    def __init__(self, reactor, config):
        self.config = config
        self.service = CarbonClientService(
            reactor,
            config['graphite_host'],
            config['graphite_port']
        )

    def get_metric_bucket(self, metric):
        return '%s.%s' % (self.config['account'], metric)

    def publish_created_url_metrics(self):
        #self.service.publish_metric(self.get_metric_bucket('created'), 1)
        pass

    def publish_expanded_url_metrics(self):
        #self.service.publish_metric(self.get_metric_bucket('expanded'), 1)
        pass

    def publish_invalid_url_metrics(self):
        #self.service.publish_metric(self.get_metric_bucket('invalid'), 1)
        pass
