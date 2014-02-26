# -*- test-case-name: shortener.tests.test_api -*-

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web import http

from aludel.service import service, handler, get_json_params


@service
class ShortenerServiceApp(object):

    def __init__(self, reactor, pool):
        pass

    @handler('/', methods=['PUT'])
    @inlineCallbacks
    def create_url(self, request):
        props = get_json_params(
            request, ['long_url', 'user_token'])
        long_url = props['long_url']
        user_token = props['user_token']

        yield request.setResponseCode(http.OK)
        returnValue({'short_url': 'foo'})
