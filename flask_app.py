# Simple Python module for retrieving historic tweets.
# Copyright (C) 2019 Marcus Burkhardt and Jörn Preuss
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
    results_headline = ''
    query = request.form.get('query', '')
    since = request.form.get('since', '')
    until = request.form.get('until', '')
    # user = {'username': 'Miguel'}

    twh = Twhist()

    fnp1 = datetime.now().strftime('%Y%m%d-%H%M%S')
    fnp2 = re.sub(r'\W', '_', query if query else '_')
    fnp3 = re.sub(r'\W', '_', since if since else '_')
    fnp4 = re.sub(r'\W', '_', until if until else '_')
    csv_file_name = f'thwist-{fnp1}-{fnp2}-{fnp3}-{fnp4}.csv'

    outpath = os.path.join('static', 'downloads')

    if not os.path.isdir(outpath):
        os.makedirs(outpath)

    csv_download_link = os.path.join(outpath, csv_file_name)

    if query and since and until:
        results = twh.get(
            query, since, until,
            limit_search=True, intervall='day',
            csv_download_link=csv_download_link)
        search_parameters = Markup(
            f'<p>Search parameters:</p><ul>'
            f'<li>Search query: {query}</li>'
            f'<li>Start date: {since}</li>'
            f'<li>End date: {until}</li></ul>')

    else:
        results = None
        # query_print = ''
        # since_print = ''
        # until_print = ''

    if type(results) == int:  # pd.DataFrame:
        # results.to_csv(csv_download_link)
        results_view = f'{results} tweets retrieved.'
        csv_download_link = Markup(
            f'<p><a href="{csv_download_link}">Download results.</a></p>')
    else:
        results_view = ''
        csv_download_link = ''

    if type(results) == pd.DataFrame or len(search_parameters) > 0:
        results_headline = Markup('<h3>Results</h3>')

    print(results)
    print(results_headline)

    return render_template(
        'twhist.html', query=query, since=since, until=until,
        results_headline=results_headline,
        results=results_view, search_parameters=search_parameters,
        csv_download_link=csv_download_link)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8048)
