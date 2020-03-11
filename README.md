  # Twitter History Search 

This tool allows you to retrieve historic Twitter data. Development is currently ongoing. You can use the tool either as Python module or as Flask web app. The functionality of the web app is by default limited to a search period of seven days. 

## Install

```console
git clone https://github.com/Digital-Methods-Tool-Lab/twitter-history-search.git
cd twitter-history-search
pip3 install requirements.txt
```

## Usage

**For using the Flask web app:**

```console
cd twitter-history-search
python3 flask_app.py
```

**For using the Python module:** Copy the directory `twhist` to your project directory.

```Python
from twhist.twhist import Twhist
twh = Twhist()
results = twh.get("Digital AND Methods", '2019-01-01', '2019-01-02', 
                  limit_search=True, intervall='day')

# to see the results as a list of lists
print(results)  

# to see the results as a pandas DataFrame
import pandas as pd
df = pd.DataFrame(results[1:], columns=results[0])
df
```

By passing `limit_search=False` an unlimited period can be queried. Three different search intervalls are implemented: `day`, `month` and `year`.


