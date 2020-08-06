from itertools import cycle
liste = [1,2,3,4,5,6,7,8,9,10]
cycle = cycle(liste)

def myfunction(x):
	y = next(cycle)
	return y