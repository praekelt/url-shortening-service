# -*- test-case-name: shortener.tests.test_shortener_service -*-

from twisted.application import strports
from twisted.internet import reactor
from twisted.python import usage
from twisted.web import server

from shortener.api import ShortenerServiceApp


DEFAULT_PORT = 'tcp:8080'


class Options(usage.Options):
    """Command line args when run as a twistd plugin"""
    optParameters = [["endpoint", "e", DEFAULT_PORT, "Port number"]]

    def postOptions(self):
        pass


def makeService(options):
    app = ShortenerServiceApp(reactor=reactor)
    site = server.Site(app.app.resource())
    return strports.service(options['endpoint'], site)
