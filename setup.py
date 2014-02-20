from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import MoePad

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md')


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='MoePad',
    version=MoePad.__version__,
    url='https://github.com/deloeating/MoePad',
    license='MIT',
    author='delo',
    tests_require=['pytest'],
    install_requires=[
        'APScheduler>=2.1.0',
        'BeautifulSoup>=3.2.1',
        'redis>=2.8.0',
        'requests>=2.2.1',
	'pytz>=2012d',
        ],
    cmdclass={'test': PyTest},
    author_email='deloeating@gmail.com',
    description='A simple weibo bot for zh.moegirl.org',
    long_description=long_description,
    packages=find_packages('MoePad'),
    package_dir={'': 'MoePad'},
    include_package_data=True,
    platforms='linux',
    # entry_points="""
    # [console_scripts]
    # mpserver = run:main
    # mpcron = MoeDj.cron:main
    # """,
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: Chinese',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: MIT License',
        'Operating System :: Linux',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    extras_require={
        'testing': ['pytest'],
    }
)
