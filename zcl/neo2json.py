import json
with open(r'../data/disease.json') as file:
	jsondata = json.load(file)
	#print(jsondata)
	for i in jsondata:
		with open(r'../data/disease3.json','a') as f:
			res = json.dumps(i)
			print(res)
			f.write(res+'<br/>')


