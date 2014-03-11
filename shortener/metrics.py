from txCarbonClient import CarbonClientService


class ShortenerCarbonClient(object):
    def __init__(self, reactor, config):
        self.config = config
        self.service = CarbonClientService(
            reactor,
            config['graphite_host'],
            config['graphite_port']
        )

    def get_count_metric(self, user_token, metric):
        return '%(account)s.%(metric)s.%(user_token)s.count' % {
            'account': self.config['account'],
            'user_token': user_token,
            'metric': metric,
        }

    def publish_created_url_metrics(self, user_token):
        metric = self.get_count_metric(user_token, 'created')
        self.service.publish_metric(metric, 1)

    def publish_expanded_url_metrics(self):
        metric = self.get_count_metric(user_token, 'expanded')
        self.service.publish_metric(metric, 1)

    def publish_invalid_url_metrics(self):
        metric = self.get_count_metric(user_token, 'invalid')
        self.service.publish_metric(metric, 1)
