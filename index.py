from __future__ import absolute_import, division, unicode_literals
import pprint
import os
import whoosh.index
import whoosh.fields
import packages
import config

pp = pprint.PrettyPrinter(indent=4)

packages = packages.get_from_db('6')

#pp.pprint(packages)

schema = whoosh.fields.Schema(name=whoosh.fields.ID(stored=True),
                              description=whoosh.fields.TEXT(stored=True),
                              summary=whoosh.fields.TEXT(stored=True),
                              arch=whoosh.fields.ID(stored=True),
                              primary_repo=whoosh.fields.ID(stored=True),
                              updates_repo=whoosh.fields.ID(stored=True),
                              version=whoosh.fields.ID(stored=True),
                              updates_version=whoosh.fields.ID(stored=True),
                              epoch=whoosh.fields.ID(stored=True),
                              updates_epoch=whoosh.fields.ID(stored=True),
                              release=whoosh.fields.ID(stored=True),
                              updates_release=whoosh.fields.ID(stored=True),
                              url=whoosh.fields.ID(stored=True),
                              location_href=whoosh.fields.ID(stored=True),
                              updates_location_href=whoosh.fields.ID(stored=True),
                              license=whoosh.fields.ID(stored=True))

index_dir = config.DATA_DIR + 'index'
if not os.path.exists(index_dir):
    os.mkdir(index_dir)
ix = whoosh.index.create_in(index_dir, schema)
ix_writer = ix.writer()

for package in packages:
    ix_writer.add_document(**package)

ix_writer.commit()
