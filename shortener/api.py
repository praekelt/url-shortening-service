# -*- test-case-name: shortener.tests.test_api -*-
from urlparse import urljoin, urlparse

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web import http

from aludel.database import get_engine
from aludel.service import service, handler, get_json_params, APIError

from shortener.models import ShortenerTables, NoShortenerTables
from shortener.keygen import generate_token
from shortener.metrics import ShortenerMetrics

DEFAULT_USER_TOKEN = 'generic-user-token'


@service
class ShortenerServiceApp(object):

    def __init__(self, reactor, config):
        self.config = config
        self.engine = get_engine(config['connection_string'], reactor)
        self.metrics = ShortenerMetrics(reactor, config)
        self.load_handlers()

    def load_handlers(self):
        self.handlers = {}
        for handler_config in self.config['handlers']:
            [(name, class_path)] = handler_config.items()
            parts = class_path.split('.')
            module = '.'.join(parts[:-1])
            class_name = parts[-1]
            handler_module = __import__(module, fromlist=[class_name])
            handler_class = getattr(handler_module, class_name)
            handler = handler_class(self.config, self.engine)
            self.handlers[name] = handler

    @handler('/api/create', methods=['PUT'])
    @inlineCallbacks
    def create_url(self, request):
        props = get_json_params(
            request, ['long_url'], ['user_token'])
        long_url = props['long_url']
        user_token = props.get('user_token', None)

        short_url = yield self.shorten_url(long_url, user_token)
        yield request.setResponseCode(http.CREATED)
        returnValue({'short_url': short_url})

    @handler('/api/init', methods=['GET'])
    @inlineCallbacks
    def init_account(self, request):
        '''
        Initializes the account and creates the database tables
        '''
        conn = yield self.engine.connect()
        account = self.config['account']
        tables = ShortenerTables(account, conn)
        try:
            already_exists = yield tables.exists()
            if not already_exists:
                yield tables.create_tables()
        finally:
            yield conn.close()

        returnValue({'created': not already_exists})

    @handler('/api/handler/<string:handler_name>', methods=['GET'])
    @inlineCallbacks
    def run_handler(self, request, handler_name):
        handler = self.handlers.get(handler_name)
        if not handler:
            request.setResponseCode(http.NOT_FOUND)
            returnValue({})
        else:
            response = yield handler.render(request)
            returnValue(response)

    @handler('/<string:short_url>', methods=['GET'])
    @inlineCallbacks
    def resolve_url(self, request, short_url):
        row = yield self.get_row_by_short_url(short_url)
        if row and row['long_url']:
            request.setResponseCode(http.MOVED_PERMANENTLY)
            request.setHeader(b"location", row['long_url'].encode('utf-8'))
            yield self.metrics.publish_expanded_url_metrics()
        else:
            request.setResponseCode(http.NOT_FOUND)
            yield self.metrics.publish_invalid_url_metrics()
        returnValue({})

    @inlineCallbacks
    def shorten_url(self, long_url, user_token=None):
        if not user_token:
            user_token = DEFAULT_USER_TOKEN

        row = yield self.get_or_create_row(long_url, user_token)
        short_url = row['short_url']
        if not row['short_url']:
            short_url = generate_token(row['id'])
            yield self.update_short_url(row['id'], short_url)
            yield self.metrics.publish_created_url_metrics()
        returnValue(urljoin(self.config['host_domain'], short_url))

    @inlineCallbacks
    def get_or_create_row(self, url, user_token):
        account = self.config['account']
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
        except NoShortenerTables:
            raise APIError('Account "%s" does not exist' % account, 200)
        finally:
            yield conn.close()

    @inlineCallbacks
    def update_short_url(self, row_id, short_url):
        account = self.config['account']
        conn = yield self.engine.connect()
        try:
            tables = ShortenerTables(account, conn)

            yield tables.update_short_url(row_id, short_url)
        finally:
            yield conn.close()

    @inlineCallbacks
    def get_row_by_short_url(self, short_url):
        account = self.config['account']
        conn = yield self.engine.connect()
        try:
            tables = ShortenerTables(account, conn)

            row = yield tables.get_row_by_short_url(short_url)
            returnValue(row)
        finally:
            yield conn.close()
