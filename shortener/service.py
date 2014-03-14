# -*- test-case-name: shortener.tests.test_shortener_service -*-
import yaml

from twisted.application import strports
from twisted.internet import reactor, service
from twisted.python import usage
from twisted.web import server

from shortener.api import ShortenerServiceApp

DEFAULT_PORT = 'tcp:8080'


class Options(usage.Options):
    """Command line args when run as a twistd plugin"""
    optParameters = [
        ["config", "c", "shortener/config.yaml", "The service config file"],
    ]

    def postOptions(self):
        pass


def makeService(options):
    config_file = options['config']
    with open(config_file, 'r') as fp:
        config = dict(yaml.safe_load(fp))

    app = ShortenerServiceApp(reactor=reactor, config=config)

    site = server.Site(app.app.resource())

    main_service = service.MultiService()

    app_service = strports.service(config.get('port', DEFAULT_PORT), site)
    app_service.setServiceParent(main_service)

    app.metrics.carbon_client.setServiceParent(main_service)

    return main_service
