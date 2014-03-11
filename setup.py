from setuptools import setup

setup(
    name="shortener",
    version="0.1",
    url='http://github.com/praekelt/url-shortening-service',
    license='BSD',
    description="An API service to shorten URLs",
    long_description=open('README.rst', 'r').read(),
    author='Praekelt',
    author_email='dev@praekelt.com',
    packages=[
        "shortener",
    ],
    package_data={},
    include_package_data=True,
    install_requires=[
        'Twisted',
        'aludel',
        'treq',
        'psycopg2',
        'txCarbonClient',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Framework :: Twisted',
    ],
)
