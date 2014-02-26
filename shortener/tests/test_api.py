import json
import treq

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import HTTPConnectionPool
from twisted.trial.unittest import TestCase
from twisted.web.server import Site

from aludel.database import MetaData
from shortener.api import ShortenerServiceApp


class TestShortenerServiceApp(TestCase):
    timeout = 5

    def _drop_tables(self):
        # NOTE: This is a blocking operation!
        md = MetaData(bind=self.service.engine._engine)
        md.reflect()
        md.drop_all()
        assert self.service.engine._engine.table_names() == []

    @inlineCallbacks
    def setUp(self):
        self.test_account = 'milton-test-account'
        cfg = {
            'host_domain': 'http://wtxt.io',
            #'connection_string': 'postgresql://shortener:shortener@localhost:5432/shortener'
            'connection_string': 'sqlite://'
        }
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.service = ShortenerServiceApp(
            reactor=reactor,
            pool=self.pool,
            config=cfg
        )
        site = Site(self.service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self.conn = yield self.service.engine.connect()
        self._drop_tables()
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.pool.closeCachedConnections)

    def make_url(self, path):
        return 'http://localhost:%s%s' % (self.listener_port, path)

    @inlineCallbacks
    def test_create_url_simple(self):
        payload = {
            'account': self.test_account,
            'api_key': 'test-api-key',
            'long_url': 'foo',
            'user_token': 'bar',
        }
        resp = yield treq.put(
            self.make_url('/'),
            data=json.dumps(payload),
            allow_redirects=False,
            pool=self.pool)

        result = yield treq.json_content(resp)
        self.assertEqual(result['short_url'], 'foo')

    @inlineCallbacks
    def test_url_shortening(self):
        yield self.service.create_tables(self.test_account)
        long_url = 'http://en.wikipedia.org/wiki/Cthulhu'
        short_url = yield self.service.shorten_url(self.test_account, long_url)
        self.assertEqual(short_url, 'http://wtxt.io/1')

    @inlineCallbacks
    def test_short_url_generation(self):
        yield self.service.create_tables(self.test_account)
        url = 'http://en.wikikipedia.org/wiki/Cthulhu'
        url1 = yield self.service.shorten_url(self.test_account, url + '1')
        url2 = yield self.service.shorten_url(self.test_account, url + '2')
        url3 = yield self.service.shorten_url(self.test_account, url + '3')
        url4 = yield self.service.shorten_url(self.test_account, url + '4')
        urls = [url1, url2, url3, url4]
        self.assertEqual(len(list(set(urls))), 4)

    @inlineCallbacks
    def test_repeat_url_generation(self):
        yield self.service.create_tables(self.test_account)
        url = 'http://en.wikikipedia.org/wiki/Cthulhu'
        url1 = yield self.service.shorten_url(self.test_account, url + '1')
        url2 = yield self.service.shorten_url(self.test_account, url + '2')
        url3 = yield self.service.shorten_url(self.test_account, url + '2')
        url4 = yield self.service.shorten_url(self.test_account, url + '1')
        urls = [url1, url2, url3, url4]
        self.assertEqual(len(list(set(urls))), 2)
