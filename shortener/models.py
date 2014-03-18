import hashlib
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import and_
from twisted.internet.defer import inlineCallbacks, returnValue

from aludel.database import TableCollection, make_table, CollectionMissingError


class ShortenerDBError(Exception):
    pass


class NoShortenerTables(ShortenerDBError):
    pass


class ShortenerTables(TableCollection):
    urls = make_table(
        Column("id", Integer(), primary_key=True),
        Column("domain", String(255), nullable=False, index=True),
        Column("user_token", String(255), nullable=False, index=True),
        Column("hash", String(32), index=True),
        Column("short_url", String(255), index=True),
        Column("long_url", Text()),
        Column("created_at", DateTime(timezone=False))
    )

    audit = make_table(
        Column("id", Integer(), primary_key=True),
        Column('url_id', Integer(), nullable=False),
        Column("hits", Integer()),
    )

    def _format_row(self, row, fields=None):
        if row is None:
            return None

        if fields is None:
            fields = set(f for f in row.keys())
        return dict((k, v) for k, v in row.items() if k in fields)

    @inlineCallbacks
    def execute_query(self, query, *args, **kw):
        try:
            result = yield super(ShortenerTables, self).execute_query(
                query, *args, **kw)
        except CollectionMissingError:
            raise NoShortenerTables(self.name)
        returnValue(result)

    @inlineCallbacks
    def get_or_create_row(self, domain, user_token, long_url):
        hashkey = hashlib.md5(''.join([
            domain, user_token, long_url
        ])).hexdigest()
        result = yield self.execute_query(
            self.urls.select().where(and_(
                self.urls.c.domain == domain,
                self.urls.c.user_token == user_token,
                self.urls.c.hash == hashkey
            )).limit(1))
        row = yield result.fetchone()

        if not row:
            yield self.execute_query(
                self.urls.insert().values(
                    domain=domain,
                    user_token=user_token,
                    hash=hashkey,
                    long_url=long_url,
                    created_at=datetime.utcnow()
                ))

            # We need to return the inserted row
            result = yield self.execute_query(
                self.urls.select().where(
                    self.urls.c.hash == hashkey
                ).limit(1))
            row = yield result.fetchone()

            yield self.create_audit(row['id'])

        returnValue(self._format_row(row))

    @inlineCallbacks
    def update_short_url(self, row_id, short_url):
        yield self.execute_query(
            self.urls.update().where(
                self.urls.c.id == row_id
            ).values(short_url=short_url))

    @inlineCallbacks
    def get_row_by_short_url(self, short_url, increment=True):
        result = yield self.execute_query(
            self.urls.select().where(
                self.urls.c.short_url == short_url
            ).limit(1))
        row = yield result.fetchone()

        if row and increment:
            yield self.execute_query(
                self.audit.update().where(
                    self.audit.c.url_id == row['id']
                ).values(hits=self.audit.c.hits + 1)
            )
        returnValue(self._format_row(row))

    @inlineCallbacks
    def create_audit(self, url_id):
        result = yield self.execute_query(
            self.audit.select().where(
                self.audit.c.url_id == url_id
            ).limit(1))
        row = yield result.fetchone()

        if not row:
            yield self.execute_query(
                self.audit.insert().values(url_id=url_id, hits=0)
            )
        returnValue({})

    @inlineCallbacks
    def get_audit_row(self, url_id):
        result = yield self.execute_query(
            self.audit.select().where(
                self.audit.c.url_id == url_id
            ).limit(1))
        row = yield result.fetchone()
        returnValue(self._format_row(row))
