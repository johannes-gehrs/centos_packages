from __future__ import absolute_import, division, unicode_literals
import os
import logging

OS_VERSIONS = ['6', '7']
DATA_DIR = '/tmp/centos_packages/'
REPO_BASE_URL = 'http://mirror.centos.org/centos/'
REPOSITORIES = ['os', 'updates', 'centosplus', 'extras', 'fasttrack']
REPOSITORIES_PRETTY = {'os': 'Base',
                       'updates': 'Updates',
                       'extras': 'Extras',
                       'fasttrack': 'Fasttrack'}
LIMIT_RESULTS = 250
CACHE_MAX_AGE = 4260
CACHE_IN_DEBUG_MODE = False


def active_repos():
    return [repo for repo in REPOSITORIES if not repo == 'centosplus']


# Logging
LOGDIR = DATA_DIR + 'log/'
LOGFILE = LOGDIR + 'centos_packages.log'
if not os.path.isdir(LOGDIR):
    os.makedirs(LOGDIR)
logging.basicConfig(filename=LOGFILE,level=logging.INFO)
