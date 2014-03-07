URL SHORTERNING SERVICE
=======================

An API service to shorten URLs

|travis|_ |coveralls|_

Install
~~~~~~~

::

    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install -e .
    (ve)$ trial shortener

.. |travis| image:: https://travis-ci.org/praekelt/url-shortening-service.png?branch=develop
.. _travis: https://travis-ci.org/praekelt/url-shortening-service

.. |coveralls| image:: https://coveralls.io/repos/praekelt/url-shortening-service/badge.png?branch=develop
.. _coveralls: https://coveralls.io/r/praekelt/url-shortening-service


Config
~~~~~~
With the `-c` parameter, you can specify a config file. The default locatation is `shortener/config.yaml`
Here's an example config file::

    host_domain: http://wtxt.io
    account: wikipedia
    connection_string: postgresql://test:shortener_test@localhost:5432/shortener_test
    port: tcp:8080

