from billiard.pool import Pool
import test1

pool = Pool(len(test1.liste))

for result in pool.imap(test1.myfunction, test1.liste):
	print(result)

