from twisted.internet.defer import inlineCallbacks, returnValue
from shortener.handlers.base import BaseApiHandler
from shortener.models import ShortenerTables
from twisted.web import http


class Dump(BaseApiHandler):
    def format_row(self, row):
        return {
            'domain': row['domain'],
            'user_token': row['user_token'],
            'short_url': row['short_url'],
            'long_url': row['long_url'],
            'created_at': row['created_at'].isoformat(),
        }

    @inlineCallbacks
    def render(self, request):
        short_url = request.args.get('url')
        conn = yield self.engine.connect()
        try:
            tables = ShortenerTables(self.config['account'], conn)
            if not short_url:
                request.setResponseCode(http.BAD_REQUEST)
                returnValue({'error': 'expected "?url=<short_url>"'})
            else:
                row = yield tables.get_row_by_short_url(short_url[0])

                if row:
                    returnValue(self.format_row(row))
                else:
                    request.setResponseCode(http.NOT_FOUND)
                    returnValue({'error': 'short url not found'})
        finally:
            yield conn.close()
