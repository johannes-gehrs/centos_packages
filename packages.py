from __future__ import absolute_import, division, unicode_literals
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

REPODATA_ARC_SUFFIX = "x86_64/"
METADATA_SUFFIX = "repodata/repomd.xml"
PACKAGE_TIMESTAMP_FILE = config.DATA_DIR + 'packages_timestamp.pickled'
YUM_REPODATA_XML_NAMESPACE = 'http://linux.duke.edu/metadata/repo'

def _find_db_link_in_xml(xml_text):
    root = ElT.fromstring(xml_text)

    for data_elmnt in root.iter('{' + YUM_REPODATA_XML_NAMESPACE + '}data'):
        if data_elmnt.attrib['type'] == 'primary_db':
            return data_elmnt.find('{' + YUM_REPODATA_XML_NAMESPACE + '}location').attrib['href']
    else:
        raise ValueError('Data not found in XML')


def _download_one(version):
    for repo in config.active_repos():
        repo_base_url = config.REPO_BASE_URL + unicode(version) + \
                        '/' + repo + '/' + REPODATA_ARC_SUFFIX
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
    for version in config.OS_VERSIONS:
        _download_one(version)


def _conn_factory(version, repo):
    conn = sqlite3.connect(config.DATA_DIR + repo + '_' + version + '.sqlite')
    conn.row_factory = sqlite3.Row
    return conn


def _primary_query_execute(conn, repo):
    c = conn.cursor()
    query = '''
            SELECT name, arch, version, epoch,
                ? AS repo, "release", summary, description, rpm_sourcerpm,
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
        prepared[name].sort(cmp=compare_rpm_versions)

    return prepared


def _not_none_epoch(epoch):
    if epoch is not None:
        return epoch
    return '0'


def _is_int(mystring):
    try:
        int(mystring)
        return True
    except ValueError:
        return False


# http://stackoverflow.com/questions/3206319/how-do-i-compare-rpm-versions-in-python
# hold my beer while I implement this
def _compare_rpm_label_fields(field1, field2):
    alphanumeric_matches = lambda field: list(re.finditer(r'[a-zA-Z0-9]+', field))
    field1_matches, field2_matches = alphanumeric_matches(field1), alphanumeric_matches(field2)

    for match_pair in zip(field1_matches, field2_matches):
        value_pair = [match.group() for match in match_pair]
        numeric_vals = [_is_int(value) for value in value_pair]

        # Non-equal types
        if not all(numeric_vals) and any(numeric_vals):
            if numeric_vals[1]:
                return -1
            if numeric_vals[0]:
                return 1

        # Equal types: Alphanumeric
        if not any(numeric_vals):
            if value_pair[0] < value_pair[1]:
                return -1
            if value_pair[0] > value_pair[1]:
                return 1

        # Equal types: Numeric
        if all(numeric_vals):
            if int(value_pair[0]) < int(value_pair[1]):
                return -1
            if int(value_pair[0]) > int(value_pair[1]):
                return 1

        assert value_pair[0] == value_pair[1]

    # Decision by no. of fields
    if len(field1_matches) < len(field2_matches):
        return -1
    if len(field1_matches) > len(field2_matches):
        return 1
    if len(field1_matches) == len(field2_matches):
        return 0

    raise RuntimeError('This code should not be reached, because one of the if paths '
                       'should have been executed.')


def compare_rpm_versions(version_one, version_two):
    label_components = ['epoch', 'version', 'release']
    for component in label_components:
        result = _compare_rpm_label_fields(version_one[component], version_two[component])
        if result != 0:
            break
    return result


def get_version(version):
    return _prepare(_read_from_dbs(version))


def get_all():
    packages_dict = {}
    for os_version in config.OS_VERSIONS:
        packages_dict[os_version] = get_version(os_version)
    return packages_dict


def minor_os_release(all_packages_dict):
    newest_package_version = all_packages_dict['centos-release'][-1]
    major_release = newest_package_version['version']
    minor_release_integer = re.match(r'.*?\.', newest_package_version['release']).group()[:-1]
    return major_release + '.' + minor_release_integer


def set_timestamp_to_now():
    now = datetime.datetime.now()
    with io.open(PACKAGE_TIMESTAMP_FILE, mode='wb') as myfile:
        pickle.dump(now, myfile)


def get_timestamp():
    with io.open(PACKAGE_TIMESTAMP_FILE, mode='rb') as myfile:
        pickle.load(myfile)


def rpm_download_url(package_version, os_version):
    return config.REPO_BASE_URL + os_version + '/' + package_version['repo'] + \
           '/' + REPODATA_ARC_SUFFIX + package_version['location_href']


def newest_versions_as_list(os_version, all_packages_dict):
    newest_versions_list = []
    for package_name in all_packages_dict[os_version]:
        newest_versions_list.append(all_packages_dict[os_version][package_name][-1])
    return newest_versions_list
