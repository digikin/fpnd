# -*- coding: utf-8 -*-
"""Setup file for fpnd node tools."""
import codecs

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


__version__ = '0.7.2-3'

# make setuptools happy with PEP 440-compliant post version
REL_TAG = __version__.replace('-', 'p')

FPND_DOWNLOAD_URL = (
    'https://github.com/sarnold/fpnd/tarball/' + REL_TAG
)


def read_file(filename):
    """
    Read a utf8 encoded text file and return its contents.
    """
    with codecs.open(filename, 'r', 'utf8') as f:
        return f.read()


setup(
    name='fpnd',
    packages=['node_tools',],
    data_files=[
        ('lib/fpnd', ['bin/fpn0-down.sh',
                      'bin/fpn0-setup.sh',
                      'bin/fpn1-down.sh',
                      'bin/fpn1-setup.sh',
                      'etc/fpnd.ini',
                      'scripts/fpnd.py',
                      'scripts/msg_responder.py',
                      'scripts/msg_subscriber.py']),
    ],
    version=__version__,
    license='AGPL-3.0',
    description='Python and shell fpnd node tools.',
    long_description=read_file('README.rst'),
    url='https://github.com/sarnold/fpnd',
    author='Stephen L Arnold',
    author_email='nerdboy@gentoo.org',
    download_url=FPND_DOWNLOAD_URL,
    keywords=['freepn', 'vpn', 'p2p'],
    install_requires=[
        'diskcache @ git+https://github.com/grantjenks/python-diskcache@v4.1.0',
        'nanoservice @ git+https://github.com/freepn/nanoservice@0.7.2p1',
        'python-daemon @ git+https://github.com/sarnold/python-daemon@0.2.1',
        'schedule @ git+https://github.com/sarnold/schedule@0.6.0p1',
        'ztcli-async @ git+https://github.com/freepn/ztcli-async@0.0.3',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Natural Language :: English',
        "Topic :: System :: Operating System Kernels :: Linux",
        "Topic :: System :: Networking",
        'Topic :: Security',
    ],
)
