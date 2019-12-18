# test_flask.py

from flask import Flask, render_template, request
from twhist.twhist import Twhist
import csv

# from app import app
app = Flask('app')


@app.route('/', methods=['GET', 'POST'])
def page():

    query = request.form.get('query', '')
    since = request.form.get('since', '')
    until = request.form.get('until', '')
    # user = {'username': 'Miguel'}

    twh = Twhist()

    if query and since and until:
        results = twh.get(
            query, since, until,
            limit_search=True, intervall='day')
    else:
        results = None

    print(results)

    return render_template(
        'twhist.html', query=query, since=since, until=until, results=results)


app.run(host='0.0.0.0', port=8080)
