from twhist.twhist import Twhist
twh = Twhist()

results = twh.get("Preuss", '2019-01-01', '2019-01-04', limit_search=True, intervall='day')
print(results)
