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
        reactor.suggestThreadPoolSize(1)
        connection_string = os.environ.get(
            "SHORTENER_TEST_CONNECTION_STRING", "sqlite://")

        self.account = 'test-account'
        cfg = {
            'host_domain': 'http://wtxt.io',
            'account': self.account,
            'connection_string': connection_string,
            'graphite_host': 'localhost',
            'graphite_port': 2001,
        }
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.service = ShortenerServiceApp(
            reactor=reactor,
            config=cfg
        )
        site = Site(self.service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self.conn = yield self.service.engine.connect()
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.pool.closeCachedConnections)

    @inlineCallbacks
    def tearDown(self):
        yield self.conn.close()
        self._drop_tables()
        yield self.listener.loseConnection()

    def make_url(self, path):
        return 'http://localhost:%s%s' % (self.listener_port, path)

    @inlineCallbacks
    def test_create_url_simple(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        payload = {
            'long_url': 'foo',
            'user_token': 'bar',
        }
        resp = yield treq.put(
            self.make_url('/api/create'),
            data=json.dumps(payload),
            allow_redirects=False,
            pool=self.pool)

        result = yield treq.json_content(resp)
        self.assertEqual(result['short_url'], 'http://wtxt.io/qr0')

    @inlineCallbacks
    def test_create_url_no_user_token(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        payload = {
            'long_url': 'foo'
        }
        resp = yield treq.put(
            self.make_url('/api/create'),
            data=json.dumps(payload),
            allow_redirects=False,
            pool=self.pool)

        result = yield treq.json_content(resp)
        self.assertEqual(result['short_url'], 'http://wtxt.io/qr0')

    @inlineCallbacks
    def test_resolve_url_simple(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        yield self.service.shorten_url(url)

        resp = yield treq.get(
            self.make_url('/qr0'),
            allow_redirects=False,
            pool=self.pool)

        self.assertEqual(resp.code, 301)
        [location] = resp.headers.getRawHeaders('location')
        self.assertEqual(location, url)

    @inlineCallbacks
    def test_resolve_url_404(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        yield self.service.shorten_url(url)

        resp = yield treq.get(
            self.make_url('/1Tx'),
            allow_redirects=False,
            pool=self.pool)

        self.assertEqual(resp.code, 404)

    @inlineCallbacks
    def test_url_shortening(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        long_url = 'http://en.wikipedia.org/wiki/Cthulhu'
        short_url = yield self.service.shorten_url(long_url)
        self.assertEqual(short_url, 'http://wtxt.io/qr0')

    @inlineCallbacks
    def test_short_url_generation(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        url1 = yield self.service.shorten_url(url + '1')
        url2 = yield self.service.shorten_url(url + '2')
        url3 = yield self.service.shorten_url(url + '3')
        url4 = yield self.service.shorten_url(url + '4')
        urls = [url1, url2, url3, url4]
        self.assertEqual(len(set(urls)), 4)

    @inlineCallbacks
    def test_repeat_url_generation(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        url1 = yield self.service.shorten_url(url + '1')
        url2 = yield self.service.shorten_url(url + '2')
        url3 = yield self.service.shorten_url(url + '2')
        url4 = yield self.service.shorten_url(url + '1')
        urls = [url1, url2, url3, url4]
        self.assertEqual(len(set(urls)), 2)

    @inlineCallbacks
    def test_resolve_url(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        yield self.service.shorten_url(url + '1')
        yield self.service.shorten_url(url + '2')
        yield self.service.shorten_url(url + '3')
        yield self.service.shorten_url(url + '4')

        result = yield self.service.get_row_by_short_url('qH0')
        self.assertEqual(result['long_url'], url + '4')

    @inlineCallbacks
    def test_short_url_sequencing(self):
        yield ShortenerTables(self.account, self.conn).create_tables()

        url = 'http://en.wikipedia.org/wiki/Cthulhu'
        urls = [''.join([url, str(a)]) for a in range(1, 10)]
        for u in urls:
            yield self.service.shorten_url(u)

        result = yield self.service.get_row_by_short_url('qs0')
        self.assertEqual(result['long_url'], url + '5')

        result = yield self.service.get_row_by_short_url('qp0')
        self.assertEqual(result['long_url'], url + '6')

    @inlineCallbacks
    def test_account_init(self):
        resp = yield treq.get(
            self.make_url('/api/init'),
            allow_redirects=False,
            pool=self.pool)
        result = yield treq.json_content(resp)
        self.assertTrue(result['created'])
