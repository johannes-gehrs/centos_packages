About
====

Update 2018-03: Now available at https://centos-packages.jogehrs.com/ after I screwed up keeping the original TLS registered.

This is a personal project by Johannes Gehrs, not associated with CentOS. I was annoyed by the fact that I could not search for CentOS packages on the web and therefore wrote this webapp.

This software is released under the MIT license and you can find the source code on
Github. The visual theme of this site is the Bootstrap-based [Superhero](http://bootswatch.com/superhero/) theme. Bootstrap includes [Glyphicons](http://glyphicons.com/) which are used in this project. The search functionality is powered by [Whoosh](https://pythonhosted.org/Whoosh/) and the pages are served by [Flask](http://flask.pocoo.org/).

The CentOS Plus repository is currently not searched because it's deactivated by default in CentOS and I wanted to keep things simple.

Installation
========

To install the software locally you need Python 2.7 and pip (consider using a virtual environment). Install the dependencies e. g.

	pip install --upgrade --requirement=requirements.txt
	
You can then run ``web.py``as a script and it will start the Flask dev server.

To download the packages and create the index you need to execute

	python manage.py --download --index --packages_timestamp
	
Notice that you may want to change the data directory in ``config.py``.
