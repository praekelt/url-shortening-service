# -*- test-case-name: shortener.tests.test_api -*-

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web import http

from aludel.database import get_engine
from aludel.service import service, handler, get_json_params, APIError
from urlparse import urljoin, urlparse

from .models import ShortenerTables, NoShortenerTables

DEFAULT_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ' +\
                   'abcdefghijklmnopqrstuvwxyz'
DEFAULT_USER_TOKEN = 'generic-user-token'


@service
class ShortenerServiceApp(object):

    def __init__(self, reactor, pool, config):
        self.config = config
        self.engine = get_engine(config['connection_string'], reactor)

    @handler('/', methods=['PUT'])
    @inlineCallbacks
    def create_url(self, request):
        props = get_json_params(
            request, ['account', 'api_key', 'long_url', 'user_token'])
        account = props['account']
        api_key = props['api_key']
        long_url = props['long_url']
        user_token = props['user_token']

        yield request.setResponseCode(http.OK)
        returnValue({'short_url': 'foo'})

    @inlineCallbacks
    def create_tables(self, account):
        conn = yield self.engine.connect()
        tables = ShortenerTables(account, conn)
        try:
            already_exists = yield tables.exists()
            if not already_exists:
                yield tables.create_tables()
        finally:
            yield conn.close()

        returnValue({'created': not already_exists})

    @inlineCallbacks
    def shorten_url(self, account, long_url, user_token=DEFAULT_USER_TOKEN):
        row = yield self.get_or_create_row(account, long_url, user_token)
        short_url = row['short_url']
        if not row['short_url']:
            short_url = self.generate_token(row['id'])
            yield self.update_short_url(account, row['id'], short_url)
        returnValue(urljoin(self.config['host_domain'], short_url))

    @inlineCallbacks
    def resolve_url(self, account, short_url):
        uri = urlparse(short_url)
        row = yield self.get_short_url(account, uri.path[1:])
        if row is None:
            returnValue(None)
        else:
            returnValue(row['long_url'])

    @inlineCallbacks
    def get_or_create_row(self, account, url, user_token):
        domain = urlparse(url).netloc
        conn = yield self.engine.connect()
        try:
            tables = ShortenerTables(account, conn)

            row = yield tables.get_or_create_row(
                domain,
                user_token,
                url
            )
            returnValue(row)
        except NoShortenerTables as e:
            raise APIError(
                'Account "%s" does not exist: %s' % (account, e.reason),
                200
            )
        finally:
            yield conn.close()

    @inlineCallbacks
    def update_short_url(self, account, row_id, short_url):
        conn = yield self.engine.connect()
        tables = ShortenerTables(account, conn)

        yield tables.update_short_url(row_id, short_url)
        yield conn.close()

    def generate_token(self, counter, alphabet=DEFAULT_ALPHABET):
        if not isinstance(counter, int):
            raise TypeError('an integer is required')
        base = len(alphabet)
        if counter == 0:
            return alphabet[0]

        digits = []
        while counter > 0:
            digits.append(alphabet[counter % base])
            counter = counter // base

        digits.reverse()
        return ''.join(digits)

    @inlineCallbacks
    def get_short_url(self, account, short_url):
        conn = yield self.engine.connect()
        try:
            tables = ShortenerTables(account, conn)

            row = yield tables.get_row_by_short_url(short_url)
            returnValue(row)
        except NoShortenerTables as e:
            raise APIError(
                'Account "%s" does not exist: %s' % (account, e.reason),
                200
            )
        finally:
            yield conn.close()
