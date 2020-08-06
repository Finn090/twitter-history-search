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
#import json
import pandas as pd
import datetime as dt
from datetime import timedelta
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
    limit = request.form.get('limit', '')
    # user = {'username': 'Miguel'}

    error = None
    results_headline = None
    results_view = None
    csv_download_link = None

    if query and since and until:
        try:
            since = dt.datetime.strptime(since, "%Y-%m-%d").date()
            until = dt.datetime.strptime(until, "%Y-%m-%d").date()
            if until-since > timedelta(days=0) and until-since <= timedelta(days=7):
                twh = Twhist(query, since, until, limit)
                if not twh.error:
                    results = twh.start_query()

                    fnp1 = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
                    fnp2 = re.sub(r'\W', '_', query if query else '_')
                    fnp3 = re.sub(r'\W', '_', str(since) if since else '_')
                    fnp4 = re.sub(r'\W', '_', str(until) if until else '_')
                    csv_file_name = f'thwist-{fnp1}-{fnp2}-{fnp3}-{fnp4}.csv'
                    outpath = os.path.join('static', 'downloads')
                    if not os.path.isdir(outpath):
                        os.makedirs(outpath)

                    csv_download_link = os.path.join(outpath, csv_file_name)
                    df = pd.DataFrame()
                    for result in results:
                        df = df.append(pd.DataFrame(result["results"]))
                    df.to_csv(csv_download_link, sep=";")

                    csv_download_link = Markup(f'<p><a href="{csv_download_link}">Download results.</a></p>')

                    results_headline = Markup('<h3>Results</h3>')

                else:
                    error = twh.error_message
            else:
                error = "Dates are either further than 7 days apart or not in the right order."
        except ValueError:
            error = "Dates were not valid."           

    return render_template(
        'twhist.html', query=query, since=since, until=until, limit=limit, error=error,
        results_headline=results_headline,
        csv_download_link=csv_download_link)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8048, debug=True)