# test_flask.py
import os
import re
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, Markup
from twhist.twhist import Twhist


# from app import app
app = Flask('app')


@app.route('/', methods=['GET', 'POST'])
def page():
    search_parameters = ''
    query = request.form.get('query', '')
    since = request.form.get('since', '')
    until = request.form.get('until', '')
    # user = {'username': 'Miguel'}


    twh = Twhist()

    if query and since and until:
        results = twh.get(
            query, since, until,
            limit_search=True, intervall='day')
        

        search_parameters = Markup('<p>Search parameters:</p><ul><li>Search query: '+str(query)+'</li><li>Start date: '+str(since)+'</li><li>End date: '+str(until)+'</li></ul>')
        query_print = Markup('<p><pre>Search query: ' + str(query) + '</pre></p>')
        since_print = Markup('<p>End date: ' + str(since) + '</p>')
        until_print = Markup('<p>End date: ' + str(until) + '</p>')
    else:
        results = None
        query_print = ''
        since_print = ''
        until_print = ''

    fnp1 = datetime.now().strftime('%Y%m%d-%H%M%S')
    fnp2 = re.sub(r'\W', '_', query if query else '_')
    fnp3 = re.sub(r'\W', '_', since if since else '_')
    fnp4 = re.sub(r'\W', '_', until if until else '_')
    csv_file_name = f'thwist-{fnp1}-{fnp2}-{fnp3}-{fnp4}.csv'

    # csv_file_path_and_name = 'downloads/' + csv_file_name
    
    if not os.path.isdir('static'):
        os.makedirs('static')

    csv_download_link = os.path.join('static', csv_file_name)

    if type(results) == pd.DataFrame:
        results.to_csv(csv_download_link)
        # results_view = results.head().to_html()
        results_view = f'{len(results)} tweets retrieved.'
        csv_download_link = Markup('<p><a href="' + csv_download_link + '">Download results.</a></p>')
    else:
        results_view = ''
        csv_download_link = ''

    print(results)


    return render_template(
        'twhist.html', query=query, since=since, until=until, 
        query_print=query_print, since_print=since_print, until_print=until_print,
        results=results_view, search_parameters=search_parameters,
        csv_download_link=csv_download_link)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8048)
