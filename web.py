from __future__ import absolute_import, division, unicode_literals
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('base.html')

if __name__ == '__main__':
    app.debug = True
    app.run()
