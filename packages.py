from __future__ import absolute_import, division, unicode_literals
import json
import pprint
import xml.etree.ElementTree as ElT
import bz2
import io
import os
import uuid
import sqlite3
import config
import re
import datetime
import pickle
import requests

REPODATA_SUFFIX = "x86_64/"
METADATA_SUFFIX = "repodata/repomd.xml"
PACKAGE_TIMESTAMP_FILE = config.DATA_DIR + 'packages_timestamp.json'


def _find_db_link_in_xml(xml_text):
    root = ElT.fromstring(xml_text)

    for data_elmnt in root.iter('{http://linux.duke.edu/metadata/repo}data'):
        if data_elmnt.attrib['type'] == 'primary_db':
            return data_elmnt.find('{http://linux.duke.edu/metadata/repo}location').attrib['href']
    else:
        raise ValueError('Data not found in XML')


def _download_one(version):
    for repo in config.active_repos():
        repo_base_url = config.REPO_BASE_URL + unicode(version) + \
                        '/' + repo + '/' + REPODATA_SUFFIX
        metadata_request_ulr = repo_base_url + METADATA_SUFFIX
        metadata_request = requests.get(metadata_request_ulr)
        db_href = _find_db_link_in_xml(metadata_request.text)

        db_request_url = repo_base_url + db_href
        db_request = requests.get(db_request_url)
        if db_request.status_code != 200:
            raise IOError('Could not get file ' + db_request_url)
        database = bz2.decompress(db_request.content)

        temp_filename = config.DATA_DIR + unicode(uuid.uuid1())
        final_filename = config.DATA_DIR + repo + '_' + version + '.sqlite'
        with io.open(temp_filename, mode='wb') as file:
            file.write(database)
        os.rename(temp_filename, final_filename)


def download():
    for version in config.VERSIONS:
        _download_one(version)


def _conn_factory(version, repo):
    conn = sqlite3.connect(config.DATA_DIR + repo + '_' + version + '.sqlite')
    conn.row_factory = sqlite3.Row
    return conn


def _primary_query_execute(conn, repo):
    c = conn.cursor()
    query = '''
            SELECT name, arch, version, epoch,
                ? AS repo, "release", summary, description,
                url, rpm_license AS license, location_href, pkgKey
            FROM packages
            WHERE 1=1
            --    AND name = 'kernel'
            --LIMIT 15
            '''
    c.execute(query, (repo,))
    return c.fetchall()


def _read_from_dbs(version):
    package_list = []
    for repo in config.active_repos():
        conn = _conn_factory(version, repo)
        package_list = package_list + _primary_query_execute(conn, repo)
    return package_list


def _prepare(package_list):
    prepared = {}
    for row in package_list:
        prepared.setdefault(row[b'name'], []).append(dict(row))

    for name in prepared:
        prepared[name].sort(key=absolute_version)

    return prepared


def absolute_version(package):
    return '_'.join([package['epoch'], package['version'], package['release']])


def get(version):
    return _prepare(_read_from_dbs(version))


def minor_os_release(version):
    conn = _conn_factory(version, 'os')
    c = conn.cursor()
    query = '''
            SELECT "release"
            FROM packages
            WHERE 1=1
                AND name = 'centos-release'
            '''
    c.execute(query)
    row = c.fetchone()
    match = re.match(r'.*?\.', row[b'release'])
    return match.group()[:-1]


def set_timestamp_to_now():
    now = datetime.datetime.now()
    with io.open(PACKAGE_TIMESTAMP_FILE, mode='wb') as file:
        pickle.dump(now, file)


def get_timestamp():
    with io.open(PACKAGE_TIMESTAMP_FILE, mode='rb') as file:
        pickle.load(file)

