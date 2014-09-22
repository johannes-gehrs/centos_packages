from __future__ import absolute_import, division, unicode_literals
from flask import Flask, render_template, redirect, url_for, request, abort, flash
import packages
import config
import index

app = Flask(__name__)
all_packages_dict = packages.get_all()


@app.context_processor
def inject_minor_os_release():
    def _minor_os_release(version):
        return packages.minor_os_release(all_packages_dict[version])

    return dict(minor_os_release=_minor_os_release)


@app.context_processor
def inject_pretty_repo_names():
    def _pretty_repo_name(repo):
        return config.REPOSITORIES_PRETTY[repo]

    return dict(pretty_repo_name=_pretty_repo_name)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html', error=error), 404


@app.route('/')
def root():
    return redirect(url_for('search', os_version='6'))


@app.route('/<os_version>', methods=['GET', 'POST'])
def search(os_version):
    if request.method == 'POST':
        search_query = request.form['search_query']
        if all_packages_dict[os_version].get(search_query):
            return redirect(url_for('package',
                                    os_version=os_version,
                                    package_name=search_query,
                                    direct=True))

        return redirect(url_for('search_results', os_version=os_version, query=search_query))
    return render_template('search.html', os_version=os_version)


def _package_versions_or_404(os_version, package_name):
    try:
        package_versions_list = all_packages_dict[os_version][package_name]
        return package_versions_list
    except KeyError:
        return abort(404)


@app.route('/<os_version>/package/<package_name>', methods=['GET'])
def package(os_version, package_name):
    package_versions_list = _package_versions_or_404(os_version, package_name)
    return render_template('package.html',
                           package=package_versions_list[-1],
                           download_url=packages.rpm_download_url(package_versions_list[-1],
                                                                  os_version),
                           os_version=os_version,
                           direct_hit=request.args.get('direct'))


@app.route('/<os_version>/package/<package_name>/versions', methods=['GET'])
def package_versions(os_version, package_name):
    package_versions_list = _package_versions_or_404(os_version, package_name)
    return render_template('versions.html',
                           versions=list(reversed(package_versions_list)),
                           os_version=os_version)


@app.route('/<os_version>/results/<query>', methods=['GET'])
def search_results(os_version, query):
    if not os_version in config.OS_VERSIONS:
        return abort(404)

    ix = index.ix_factory(os_version)
    searcher = ix.searcher()
    parser = index.parser_factory(ix)

    results = searcher.search(parser.parse(query), limit=config.LIMIT_RESULTS)

    if len(results) >= config.LIMIT_RESULTS:
        maximum_reached = True
    else:
        maximum_reached = False

    package_versions_list = [all_packages_dict[os_version][result['name']][-1] for result in
                             results]

    return render_template('results.html', os_version=os_version, results=package_versions_list,
                           query=query, maximum_reached=maximum_reached)


if __name__ == '__main__':
    app.debug = True
    app.run()
