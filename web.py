from __future__ import absolute_import, division, unicode_literals
from flask import Flask, render_template, redirect, url_for, request, abort, flash
import packages

app = Flask(__name__)
all_packages_dict = packages.get_all()


@app.context_processor
def inject_minor_os_release():
    def _minor_os_release(version):
        return packages.minor_os_release(all_packages_dict[version])
    return dict(minor_os_release=_minor_os_release)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html', error=error), 404


@app.route('/')
def root():
    return redirect(url_for('search', os_version='6'))


@app.route('/<os_version>', methods=['GET', 'POST'])
def search(os_version):
    if request.method == 'POST':
        search_term = request.form['search_term']
        if all_packages_dict[os_version].get(search_term):
            return redirect(url_for('package',
                                    os_version=os_version,
                                    package_name=search_term,
                                    direct=True
            ))
    return render_template('search.html', os_version=os_version)


def _package_versions_or_404(os_version, package_name):
    package_versions_list = all_packages_dict[os_version].get(package_name)
    if not package_versions_list:
        return abort(404)
    return package_versions_list


@app.route('/<os_version>/package/<package_name>', methods=['GET'])
def package(os_version, package_name):
    package_versions_list = _package_versions_or_404(os_version, package_name)
    return render_template('package.html',
                           package=package_versions_list[-1],
                           download_url=packages.rpm_download_url(package_versions_list[-1], os_version),
                           os_version=os_version,
                           direct_hit = request.args.get('direct'))


@app.route('/<os_version>/package/<package_name>/versions', methods=['GET'])
def package_versions(os_version, package_name):
    package_versions_list = _package_versions_or_404(os_version, package_name)
    return render_template('versions.html',
                           versions=list(reversed(package_versions_list)),
                           os_version=os_version)


if __name__ == '__main__':
    app.debug = True
    app.run()
