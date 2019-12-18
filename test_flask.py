# test_flask.py

from flask import Flask, render_template, request
# from app import app
app = Flask('app')


@app.route('/', methods=['GET', 'POST'])
def page():

    a = request.form.get('a', '')
    b = request.form.get('b', '')
    # user = {'username': 'Miguel'}
    return render_template('twhist.html', a=a, b=b)


app.run(host='0.0.0.0', port=8080)
