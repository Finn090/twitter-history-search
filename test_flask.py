# test_flask.py

import re
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request
from twhist.twhist import Twhist


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

    fnp1 = datetime.now().strftime('%Y%m%d_%H%M%S')
    fnp2 = re.sub(r'\W', '_', query if query else '_')
    fnp3 = re.sub(r'\W', '_', since if since else '_')
    fnp4 = re.sub(r'\W', '_', until if until else '_')
    csv_file_name = f'thwist_{fnp1}_{fnp2}_{fnp3}_{fnp4}.csv'

    # csv_file_path_and_name = 'downloads/' + csv_file_name
    csv_download_link = 'static/' + csv_file_name

    if type(results) == pd.DataFrame:
        results.to_csv(csv_download_link)
        results_view = results.head().to_html()
    else:
        results_view = '-'

    print(results)

    return render_template(
        'twhist.html', query=query, since=since, until=until,
        results=results_view,
        csv_download_link=csv_download_link)


app.run(host='0.0.0.0', port=8080)
