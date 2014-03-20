import os
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from aludel.database import get_engine, MetaData
from aludel.tests.doubles import FakeReactorThreads
from shortener.models import ShortenerTables


class TestShortenerServiceApp(TestCase):
    timeout = 5

    def _drop_tables(self):
        # NOTE: This is a blocking operation!
        md = MetaData(bind=self.engine._engine)
        md.reflect()
        md.drop_all()
        assert self.engine._engine.table_names() == []

    def setUp(self):
        reactor.suggestThreadPoolSize(1)
        connection_string = os.environ.get(
            "SHORTENER_TEST_CONNECTION_STRING", "sqlite://")
        self.engine = get_engine(
            connection_string, reactor=FakeReactorThreads())
        self._drop_tables()
        self.conn = self.successResultOf(self.engine.connect())

    @inlineCallbacks
    def tearDown(self):
        yield self.conn.close()
        self._drop_tables()

    def test_tables_create(self):
        tables = ShortenerTables('test-account', self.conn)
        self.successResultOf(tables.create_tables())

    @inlineCallbacks
    def test_get_or_create_row(self):
        tables = ShortenerTables('test-account', self.conn)
        yield tables.create_tables()

        row = yield tables.get_or_create_row(
            'wiki.org', 'test', 'http://wiki.org/test/')
        self.assertEqual(row['domain'], 'wiki.org')
        self.assertEqual(row['short_url'], None)
        self.assertEqual(row['user_token'], 'test')
        self.assertEqual(row['long_url'], 'http://wiki.org/test/')
        self.assertEqual(row['id'], 1)

        row = yield tables.get_or_create_row(
            'wiki.org', 'test', 'http://wiki.org/test/')
        self.assertEqual(row['id'], 1)

        audit = yield tables.get_audit_row(1)
        self.assertEqual(audit['hits'], 0)

    @inlineCallbacks
    def test_update_short_url(self):
        tables = ShortenerTables('test-account', self.conn)
        yield tables.create_tables()

        row = yield tables.get_or_create_row(
            'wiki.org', 'test', 'http://wiki.org/test/')
        self.assertEqual(row['domain'], 'wiki.org')
        self.assertEqual(row['short_url'], None)
        self.assertEqual(row['id'], 1)

        yield tables.update_short_url(1, 'aaa')
        row = yield tables.get_or_create_row(
            'wiki.org', 'test', 'http://wiki.org/test/')

        self.assertEqual(row['domain'], 'wiki.org')
        self.assertEqual(row['short_url'], 'aaa')
        self.assertEqual(row['id'], 1)

        audit = yield tables.get_audit_row(1)
        self.assertEqual(audit['hits'], 0)

    @inlineCallbacks
    def test_resolve_url(self):
        tables = ShortenerTables('test-account', self.conn)
        yield tables.create_tables()

        yield tables.get_or_create_row(
            'wiki.org', 'test', 'http://wiki.org/test/')
        yield tables.update_short_url(1, 'aaa')

        row = yield tables.get_row_by_short_url('aaa')

        self.assertEqual(row['domain'], 'wiki.org')
        self.assertEqual(row['short_url'], 'aaa')
        self.assertEqual(row['id'], 1)

        audit = yield tables.get_audit_row(1)
        self.assertEqual(audit['hits'], 1)

        #multiple hits
        for i in range(0, 10):
            yield tables.get_row_by_short_url('aaa')

        audit = yield tables.get_audit_row(1)
        self.assertEqual(audit['hits'], 11)
