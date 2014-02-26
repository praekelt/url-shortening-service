from twisted.application.service import ServiceMaker

serviceMaker = ServiceMaker(
    'shortener-service', 'shortener.service',
    'RESTful service for url shortener.', 'shortener-service')
