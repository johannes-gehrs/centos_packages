from __future__ import absolute_import, division, unicode_literals
from flask import Flask
import requests
import xml.etree.ElementTree as ElT
import bz2
import io
import os
import uuid
import sqlite3
import pprint

pp = pprint.PrettyPrinter(indent=4)
app = Flask(__name__)

DATA_DIR = '/tmp/centos_packages/'
BASE_URL = "http://mirror.centos.org/centos/"
REPODATA_SUFFIX = "x86_64/"
METADATA_SUFFIX = "repodata/repomd.xml"
REPOSITORIES = ['os', 'updates', 'centosplus', 'extras', 'fasttrack']


def find_db_link_in_xml(xml_text):
    root = ElT.fromstring(xml_text)

    for data_e in root.iter('{http://linux.duke.edu/metadata/repo}data'):
        if data_e.attrib['type'] == 'primary_db':
            return data_e.find('{http://linux.duke.edu/metadata/repo}location').attrib['href']
    else:
        raise ValueError('Data not found in XML')


def get_repo_data_from_web(version):
    for repo in REPOSITORIES:
        repo_base_url = BASE_URL + unicode(version) + '/' + repo + '/' + REPODATA_SUFFIX
        metadata_request_ulr = repo_base_url + METADATA_SUFFIX
        metadata_request = requests.get(metadata_request_ulr)
        db_href = find_db_link_in_xml(metadata_request.text)

        db_request_url = repo_base_url + db_href
        db_request = requests.get(db_request_url)
        if db_request.status_code != 200:
            raise IOError('Could not get file ' + db_request_url)
        database = bz2.decompress(db_request.content)

        temp_filename = DATA_DIR + unicode(uuid.uuid1())
        final_filename = DATA_DIR + repo + '_' + version + '.sqlite'
        with io.open(temp_filename, mode='wb') as file:
            file.write(database)
        os.rename(temp_filename, final_filename)

#get_repo_data_from_web('6')

def conn_factory(version, repo):
    conn =  sqlite3.connect(DATA_DIR + repo + '_' + version + '.sqlite')
    return conn


def primary_data_query_execute(conn):
    c = conn.cursor()
    query = '''
            SELECT name, arch, version, epoch,
                "release", summary, description,
                url, rpm_license, location_href
            FROM packages
            WHERE 1=1
            LIMIT 5
            '''
    c.execute(query)
    return c.fetchall()

def updates_data_query_execute(conn, name):
    c = conn.cursor()
    query = '''
            SELECT name,
                max(
                CASE WHEN epoch IS NULL THEN 0 ELSE epoch end || '-'
                    || version || '-'
                    || release) absolute_version,
                version, epoch, release, location_href
            FROM packages
            WHERE 1=1
                AND name = ?
            GROUP BY name
            '''
    c.execute(query, (name,))
    return c.fetchall()


def read_primary_data_from_db(version):
    conn_os = conn_factory(version, 'os')

    conn_extras = conn_factory(version, 'extras')
    conn_centosplus = conn_factory(version, 'centosplus')

    base_data = [e + ('base',) for e in primary_data_query_execute(conn_os)]
    extras_data = [e + ('extras',) for e in primary_data_query_execute(conn_extras)]
    #centosplus_data = [e + ('centosplus',) for e in primary_data_query_execute(conn_centosplus)]
    return base_data + extras_data


def read_matching_updates_from_db(version, name):
    conn_fasttrack = conn_factory(version, 'fasttrack')
    conn_updates = conn_factory(version, 'updates')

    base_updates_data = [e + ('updates',) for e in updates_data_query_execute(conn_updates, name)]
    fasttrack_data = [e + ('fasttrack',) for e in updates_data_query_execute(conn_fasttrack, name)]
    return base_updates_data + fasttrack_data


def prepared_repodata(version):
    primary_data = read_primary_data_from_db(version)
    prepared_data = []

    for row in primary_data:
        package = {
            'name': row[0],
            'arch': row[1],
            'version': row[2],
            'epoch': row[3],
            'release': row[4],
            'summary': row[5],
            'description': row[6],
            'url': row[7],
            'license': row[8],
            'location_href': row[9],
            'primary_repo': row[10]
        }
        matching_updates = read_matching_updates_from_db(version, package['name'])
        if matching_updates:
            if len(matching_updates) > 1:
                raise RuntimeError("There shouldn't be more than one matching update")
            matching_update = matching_updates[0]
            package_update = {'updates_version': matching_update[2],
                              'updates_epoch': matching_update[3],
                              'updates_release': matching_update[4],
                              'updates_location_href': matching_update[5],
                              'updates_repo': matching_update[6]}
            package.update(package_update)
        prepared_data.append(package)

    return prepared_data


@app.route('/')
def hello_world():
    return 'Hello World!'

#if __name__ == '__main__':
#    app.run()

pp.pprint(prepared_repodata('6'))
