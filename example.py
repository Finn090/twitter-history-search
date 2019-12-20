from twhist.twhist import Twhist
twh = Twhist()
results = twh.get("Digital AND Methods", '2019-01-01', '2019-01-02', limit_search=True, intervall='day')
print(results)
