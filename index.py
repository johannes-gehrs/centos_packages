from __future__ import absolute_import, division, unicode_literals
import pprint
import os
import whoosh.index
import whoosh.fields
import whoosh.qparser
import packages
import config

pp = pprint.PrettyPrinter(indent=4)

INDICES_DIR = config.DATA_DIR + 'index'

def _index_dir(version):
    return INDICES_DIR + '/' + version


def _write_index(version):
    packages_dict = packages.get_version(version)

    schema = whoosh.fields.Schema(name=whoosh.fields.TEXT(stored=True, field_boost=12.0),
                                  description=whoosh.fields.TEXT,
                                  summary=whoosh.fields.TEXT(field_boost=2.5),
                                  arch=whoosh.fields.ID,
                                  version=whoosh.fields.ID,
                                  epoch=whoosh.fields.ID,
                                  release=whoosh.fields.ID,
                                  url=whoosh.fields.ID,
                                  location_href=whoosh.fields.ID,
                                  license=whoosh.fields.ID,
                                  repo=whoosh.fields.ID(stored=True),
                                  pkgKey=whoosh.fields.NUMERIC,
                                  rpm_sourcerpm=whoosh.fields.ID)

    index_dir = _index_dir(version)
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    ix = whoosh.index.create_in(index_dir, schema)
    ix_writer = ix.writer()

    for name in packages_dict:
        ix_writer.add_document(**packages_dict[name][-1])
    ix_writer.commit()


def write_indices():
    for version in config.OS_VERSIONS:
        _write_index(version)


def ix_factory(version):
    index_dir = _index_dir(version)
    return whoosh.index.open_dir(index_dir)


def parser_factory(ix):
    return whoosh.qparser.MultifieldParser(["name", "summary", 'description'], ix.schema)
