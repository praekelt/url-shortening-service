import hashlib
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import and_
from twisted.internet.defer import inlineCallbacks, returnValue

from aludel.database import TableCollection, make_table, CollectionMissingError


class ShortenerDBError(Exception):
    pass


class NoShortenerTables(ShortenerDBError):
    pass


class ShortenerTables(TableCollection):
    shortened_urls = make_table(
        Column("id", Integer(), primary_key=True),
        Column("domain", String(255), nullable=False, index=True),
        Column("user_token", String(255), nullable=False, index=True),
        Column("hash", String(32), index=True),
        Column("short_url", String(255)),
        Column("long_url", String(255)),
        Column("created_at", DateTime(timezone=False))
    )

    def _format_row(self, row, fields=None):
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
            self.shortened_urls.select().where(and_(
                self.shortened_urls.c.domain == domain,
                self.shortened_urls.c.user_token == user_token,
                self.shortened_urls.c.hash == hashkey
            )).limit(1))
        row = yield result.fetchone()

        if not row:
            yield self.execute_query(
                self.shortened_urls.insert().values(
                    domain=domain,
                    user_token=user_token,
                    hash=hashkey,
                    long_url=long_url,
                    created_at=datetime.utcnow()
                ))

            # We need to return the inserted row
            result = yield self.execute_query(
                self.shortened_urls.select().where(
                    self.shortened_urls.c.hash == hashkey
                ).limit(1))
            row = yield result.fetchone()

        returnValue(self._format_row(row))

    @inlineCallbacks
    def update_short_url(self, row_id, short_url):
        yield self.execute_query(
            self.shortened_urls.update().where(
                self.shortened_urls.c.id == row_id
            ).values(short_url=short_url))
