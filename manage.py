from __future__ import absolute_import, division, unicode_literals
import argparse
import sys
import time
import config
import packages
import index


def _stopwatch(start_time):
    return "Done. Time elapsed in seconds: " + unicode(time.time() - start_time)


def _download():
    start_time = time.time()
    print "Starting downloads. This can take up to a few minutes."
    packages.download()
    print _stopwatch(start_time)


def _index_refresh():
    start_time = time.time()
    print "Starting indexing. This can take a minute."
    index.write_indices()
    print _stopwatch(start_time)


def _search(term, version):
    if not version in config.OS_VERSIONS:
        print "Unknown version."
        sys.exit(1)

    ix = index.ix_factory(version)
    searcher = ix.searcher()
    parser = index.parser_factory(ix)

    start_time = time.time()
    results = searcher.search(parser.parse(term))
    for result in results:
        print result
    print _stopwatch(start_time)


def _set_package_timestamp_to_now():
    packages.set_timestamp_to_now()
    print "Done setting package data timestamp to current time and date."


parser = argparse.ArgumentParser(description='Manage Centos Packages stuff.')
parser.add_argument('--download',
                    help='Download repo data from web.',
                    action='store_true')
parser.add_argument('--index',
                    help='Recreate the search index from the repo data.',
                    action='store_true')
parser.add_argument('--search',
                    help='Search for a term from the commmand line.',
                    action='store')
parser.add_argument('--version',
                    help='Only with "search" and "timestamp" option. '
                         'Specifies version to search in.',
                    action='store')
parser.add_argument('--packages_timestamp',
                    help="Sets timestamp of package data to now which indicats that "
                         "they are fresh to webapp.",
                    action='store_true')
args = parser.parse_args()

if not any([args.download, args.index, args.search, args.packages_timestamp]):
    print "At least one option is required. See --help."
    sys.exit(1)


def _requires_version():
    if not args.version:
        print "Please specify version."
        sys.exit(1)


if args.download:
    _download()

if args.index:
    _index_refresh()

if args.search:
    _requires_version()
    _search(args.search, args.version)

if args.packages_timestamp:
    _set_package_timestamp_to_now()
