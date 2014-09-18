from __future__ import absolute_import, division, unicode_literals
import pprint
import packages
from flask import Flask, render_template, redirect, url_for, request, abort

app = Flask(__name__)
packages_dict = packages.get_all()
pp = pprint.PrettyPrinter(indent=4)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html', error=error), 404


@app.route('/')
def root():
    return redirect(url_for('search', version='6'))


@app.route('/<version>', methods=['GET', 'POST'])
def search(version):
    if request.method == 'POST':
        search_term = request.form['search_term']
        if packages_dict[version].get(search_term):
            return redirect(url_for('package', version=version, name=search_term))
    return render_template('search.html', version=version)


@app.route('/<version>/package/<name>', methods=['GET'])
def package(version, name):
    package_dict = packages_dict[version].get(name)
    if not package_dict:
        return abort(404)
    return 'Lolwut?'


if __name__ == '__main__':
    app.debug = True
    app.run()
