from __future__ import absolute_import, division, unicode_literals

OS_VERSIONS = ['6', '7']
DATA_DIR = '/tmp/centos_packages/'
REPO_BASE_URL = 'http://mirror.centos.org/centos/'
REPOSITORIES = ['os', 'updates', 'centosplus', 'extras', 'fasttrack']
REPOSITORIES_PRETTY = {'os': 'Base',
                       'updates': 'Updates',
                       'extras': 'Extras',
                       'fasttrack': 'Fasttrack'}


def active_repos():
    return [repo for repo in REPOSITORIES if not repo == 'centosplus']
