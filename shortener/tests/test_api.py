import json
import treq

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import HTTPConnectionPool
from twisted.trial.unittest import TestCase
from twisted.web.server import Site

from shortener.api import ShortenerServiceApp


class TestShortenerServiceApp(TestCase):
    timeout = 5

    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.service = ShortenerServiceApp(reactor=reactor, pool=self.pool)
        site = Site(self.service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.pool.closeCachedConnections)

    def make_url(self, path):
        return 'http://localhost:%s%s' % (self.listener_port, path)

    @inlineCallbacks
    def test_create_url_simple(self):
        payload = {
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

    def test_url_shortening(self):
        long_url = 'http://en.wikipedia.org/wiki/Cthulhu'
        short_url = self.service.shorten_url(long_url)
        self.assertEqual(short_url, 'http://wtxt.io/000')
