import json
import os
import treq

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import HTTPConnectionPool
from twisted.trial.unittest import TestCase
from twisted.web.server import Site

from aludel.database import MetaData
from shortener.api import ShortenerServiceApp
from shortener.models import ShortenerTables
from shortener.metrics import CarbonClientService
from shortener.tests.doubles import (
    DisconnectingStringTransport, StringTransportClientEndpoint)


class TestHandlers(TestCase):
    timeout = 5

    def _drop_tables(self):
        # NOTE: This is a blocking operation!
        md = MetaData(bind=self.service.engine._engine)
        md.reflect()
        md.drop_all()
        assert self.service.engine._engine.table_names() == []

    @inlineCallbacks
    def setUp(self):
        reactor.suggestThreadPoolSize(1)
        connection_string = os.environ.get(
            "SHORTENER_TEST_CONNECTION_STRING", "sqlite://")

        self.account = 'test-account'
        cfg = {
            'host_domain': 'http://wtxt.io',
            'account': self.account,
            'connection_string': connection_string,
            'graphite_endpoint': 'tcp:www.example.com:80',
            'handlers': [
                {'dump': 'shortener.handlers.dump.Dump'},
            ],
        }
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.service = ShortenerServiceApp(
            reactor=reactor,
            config=cfg
        )

        self.tr = DisconnectingStringTransport()
        endpoint = StringTransportClientEndpoint(reactor, self.tr)
        self.service.metrics.carbon_client = CarbonClientService(endpoint)
        self.service.metrics.carbon_client.startService()
        yield self.service.metrics.carbon_client.connect_d

        site = Site(self.service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self._drop_tables()
        self.conn = yield self.service.engine.connect()
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.pool.closeCachedConnections)

    def make_url(self, path):
        return 'http://localhost:%s%s' % (self.listener_port, path)

    @inlineCallbacks
    def test_api_dump(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        yield self.service.shorten_url(url, 'test-user')
        yield treq.get(
            self.make_url('/qr0'),
            allow_redirects=False,
            pool=self.pool)

        resp = yield treq.get(
            self.make_url('/api/handler/dump?url=qr0'),
            allow_redirects=False,
            pool=self.pool)

        self.assertEqual(resp.code, 200)
        result = yield treq.json_content(resp)
        self.assertEqual(result['user_token'], 'test-user')
        self.assertEqual(result['short_url'], 'qr0')
        self.assertEqual(result['long_url'], url)
        self.assertEqual(result['domain'], 'en.wikipedia.org')

    @inlineCallbacks
    def test_api_dump_invalid_querystring(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        yield self.service.shorten_url(url, 'test-user')
        yield treq.get(
            self.make_url('/qr0'),
            allow_redirects=False,
            pool=self.pool)

        resp = yield treq.get(
            self.make_url('/api/handler/dump'),
            allow_redirects=False,
            pool=self.pool)

        self.assertEqual(resp.code, 404)
