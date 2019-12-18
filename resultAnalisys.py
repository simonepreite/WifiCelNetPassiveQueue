import os
import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
from statistics import mean
import pprint


def convertVecToJson(src, dst):
	for file in os.listdir(src):
		if file.split(".")[-1]=="vec":
			jsonFile = dst + file[:-3]+"json "
			vecFile = src + file
			os.system("scavetool x -f 'module(\"*\")' -o " + jsonFile + " -F JSON " + vecFile)


def running_avg(x):
    return np.cumsum(x) / np.arange(1, x.size + 1)


def listJsonVec(jsonRoot, transiente):
	filesDict = {}
	for file in os.listdir(jsonRoot):
		with open(jsonRoot + file) as jsonFile:
			tmpJson = json.load(jsonFile)
			firstKey = list(tmpJson.keys())[0]
			#seed = 7
			#if transiente:
			seed = tmpJson[firstKey]["attributes"]["iterationvars"].split(",")[0].split("=")[1]
			deadline = int(tmpJson[firstKey]["attributes"]["iterationvars"].split(",")[1].split("=")[1])
			#else:
			#	deadline = int(tmpJson[firstKey]["attributes"]["iterationvars"].split("=")[1])
			filesDict.setdefault(deadline, {}).setdefault(seed, {}).setdefault("serviceTime", {})
			filesDict.setdefault(deadline, {}).setdefault(seed, {}).setdefault("responseTime", {})
			filesDict.setdefault(deadline, {}).setdefault(seed, {}).setdefault("lifeTime", {})
			for vec in tmpJson[firstKey]["vectors"]:
				if "lifeTime" in vec["name"]:
					filesDict[deadline][seed]["lifeTime"].setdefault(vec["name"],(vec["time"], vec["value"]))
				if "response" in vec["name"]:
					filesDict[deadline][seed]["responseTime"].setdefault(vec["module"],(vec["time"], vec["value"]))
				elif "ervic" in vec["name"] and "REMOTE" not in vec["module"]:
					filesDict[deadline][seed]["serviceTime"].setdefault(vec["module"], (vec["time"], vec["value"]))
				elif "storeWifiTime" in vec["name"] or "storeCelTime" in vec["name"] or "storeDeadline" in vec["name"]:
					filesDict[deadline][seed]["serviceTime"].setdefault(vec["name"], (vec["time"], vec["value"]))
	return filesDict


def quantizeData(timeData, valData, step=10.0):
	maxIndex = np.argmax([len(v) for v in timeData])
	windows = np.arange(start=0.0, stop=timeData[maxIndex][len(timeData[maxIndex])-1], step=step)
	
	windowedData = {}
	for i in range(len(timeData)):
		timeVals = timeData[i]
		vals = valData[i]
		ids = np.digitize(timeVals, windows).tolist()
		for id, time, val in zip(ids, timeVals, vals):
			windowedData.setdefault(id, []).append((time, val))
	quantizedTimes = []
	quantizedValues = []
	
	count = 0
	for key in sorted(windowedData.keys()):
		count += 1
		if count % 5 == 0:
			continue
		valueList = windowedData[key]
		times = np.array(list(map(lambda e: e[0], valueList)))
		values = np.array(list(map(lambda e: e[1], valueList)))
		quantizedTimes.append(np.mean(times))
		quantizedValues.append(np.mean(values))
	return np.array(quantizedTimes), np.array(quantizedValues)


def checkMean(jsonRawData):
	wifiMean = np.array(jsonRawData[33]["25"]["serviceTime"]["accWifiService:vector"][1])
	celMean = np.array(jsonRawData[33]["25"]["serviceTime"]["accCelService:vector"][1])
	print(np.mean(wifiMean))
	print(np.mean(running_avg(wifiMean)))
	print(np.mean(celMean))
	print(np.mean(running_avg(celMean)))

def plotServiceTime(jsonRawData):
	print("plotServiceTime")
	switchMode = ["storeWifiTime:vector", "storeCelTime:vector"]
	deadlineStable = ["storeDeadline:vector"]
	serviceTimes = ["WifiCelNetPassiveQueue.WIFI", "WifiCelNetPassiveQueue.CELL", "WifiCelNetPassiveQueue.LOCAL"]
	for deadline in jsonRawData:
		for metric in serviceTimes:
			for seed, values in jsonRawData[deadline].items():
				plt.plot(values["serviceTime"][metric][0], running_avg(np.array(values["serviceTime"][metric][1])), label=metric+" "+str(deadline/60))
	plt.legend()
	plt.show()		


def getMetric(jsonRawData, type, metric):
	listTime = []
	listValue = []
	for deadline in jsonRawData:
		for seed, values in jsonRawData[deadline].items():
			listTime.append(values[type][metric][0])
			listValue.append(values[type][metric][1])
	return listTime, listValue


def plotMeanEnergyConsuption(jsonRawData):
	deadlines = []
	meanEnergyConsuptions = []
	#seed = 7
	for deadline, value in jsonRawData.items():
		print("deadline: {}".format(deadline))
		meanEnergyConsuptionacc = []
		for seed, val in value.items():
			#TotalLocalActiveTime = val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][0][-1] - val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][0][0]
			TotalLocalActiveTime = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1])
			TotalWifiActiveTime = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1])
			TotalCelActiveTime = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1])#val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][0][-1] - val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][0][0]#np.sum(val["serviceTime"]["storeCelTime:vector"][1])
			#TotalConsuptionWifi = np.mean(np.multiply(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1],0.0175) / 40)
			#TotalConsuptionCel = np.mean(np.multiply(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1],0.00625) / 400)
			#TotalConsuptionLocal = np.mean(np.multiply(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1],0.4) / 5)
			#TotalConsuptionWifi = np.mean(np.multiply(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1],0.0175) / 40)
			#TotalConsuptionCel = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1]) * 0.00625 / TotalCelActiveTime
			#TotalConsuptionLocal = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1]) * 0.4 / TotalLocalActiveTime
			#print("seed: {}, Total wifi Time: {}, Total Cel Time: {}, wifi Sum * 0.7:  {}, cel Sum * 2.5: {}, local Sum * 2: {}, num Job in local: {}".format(seed, TotalWifiActiveTime, TotalCelActiveTime, np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1]) * 0.7, np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1]) * 2.5, np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1]) * 2, 	len(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1])))
			sumJob = (len(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1])+len(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1])+len(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1]))
			#meanEnergyConsuptionacc.append(1 / (1/120) * np.sum([TotalConsuptionWifi, TotalConsuptionCel, TotalConsuptionLocal]) / sumJob)
			meanEnergyConsuptionacc.append(((TotalWifiActiveTime)*28+(TotalCelActiveTime)*1000+(TotalLocalActiveTime)*10)/sumJob)
		meanEnergyConsuptions.append(np.mean(meanEnergyConsuptionacc))
		deadlines.append(deadline)
	matrixMeanEnergyConsuptions = np.column_stack((deadlines, meanEnergyConsuptions))
	matrixMeanEnergyConsuptions = matrixMeanEnergyConsuptions[matrixMeanEnergyConsuptions[:,0].argsort()]
	plt.plot(matrixMeanEnergyConsuptions[:,0].tolist(), matrixMeanEnergyConsuptions[:,1].tolist())
	"""xs = matrixMeanEnergyConsuptions[:,0]
	ys = matrixMeanEnergyConsuptions[:,1]
	coeff = np.polyfit(xs.flatten(), ys.flatten(), 5)
	p = np.poly1d(coeff)
	plt.plot(xs.tolist(), p(xs).tolist())"""
	return matrixMeanEnergyConsuptions
	
def plotMeanResponseTime1(jsonRawData):
	deadlines = []
	meanResponseTimes = []
	#seed = 7
	# non avendo distinzione tra coda wifi e coda cellulate suppongo che la coda offload sia una buona indicazione media di entrambe, quindi la considero come un'unica metrica 
	TotalLocalActiveTime = 3500000
	for deadline, value in jsonRawData.items():
		meanResponseTimeacc = []
		for seed, val in value.items():
			TotallifeTimeActiveTime = np.mean(val["lifeTime"]["lifeTime:vector"][1])
			meanResponseTimeacc.append(TotallifeTimeActiveTime)
		tempMean = np.mean(meanResponseTimeacc)/60
		print(tempMean)
		meanResponseTimes.append(tempMean)
		deadlines.append(deadline/60)
	matrixMeanResponseTimes = np.column_stack((deadlines, meanResponseTimes))
	matrixMeanResponseTimes = matrixMeanResponseTimes[matrixMeanResponseTimes[:,0].argsort()]
	xs = matrixMeanResponseTimes[:,0]
	ys = matrixMeanResponseTimes[:,1]
	plt.plot(xs.tolist(), ys.tolist())
	"""coeff = np.polyfit(xs.flatten(), ys.flatten(), 5)
	p = np.poly1d(coeff)
	plt.plot(xs.tolist(), p(xs).tolist())"""
	return matrixMeanResponseTimes

def plotMeanResponseTime(jsonRawData):
	deadlines = []
	meanResponseTimes = []
	#seed = 7
	# non avendo distinzione tra coda wifi e coda cellulate suppongo che la coda offload sia una buona indicazione media di entrambe, quindi la considero come un'unica metrica 
	TotalLocalActiveTime = 1#3500000
	for deadline, value in jsonRawData.items():
		meanResponseTimeacc = []
		for seed, val in value.items():
			TotalWifiActiveTime = 1#np.sum(val["serviceTime"]["storeWifiTime:vector"][1])
			TotalCelActiveTime = 1#np.sum(val["serviceTime"]["storeCelTime:vector"][1])
			meanResponseTimeacc.append((np.sum([np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.WIFI"][1])/TotalWifiActiveTime, np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.CELL"][1])/TotalCelActiveTime, np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.REMOTE"][1])/TotalLocalActiveTime, np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.LOCAL"][1])/TotalLocalActiveTime]))/60)
		meanResponseTimes.append(np.mean(meanResponseTimeacc))
		deadlines.append(deadline/60)
	matrixMeanResponseTimes = np.column_stack((deadlines, meanResponseTimes))
	matrixMeanResponseTimes = matrixMeanResponseTimes[matrixMeanResponseTimes[:,0].argsort()]
	xs = matrixMeanResponseTimes[:,0]
	ys = matrixMeanResponseTimes[:,1]
	plt.plot(xs.tolist(), ys.tolist())
	coeff = np.polyfit(xs.flatten(), ys.flatten(), 5)
	p = np.poly1d(coeff)
	plt.plot(xs.tolist(), p(xs).tolist())
	return matrixMeanResponseTimes


def plotERWP(matrixMeanResponseTimes, matrixMeanEnergyConsuptions, w=0.5):
	ERWPValues = np.multiply(np.power(matrixMeanResponseTimes[:,0], w), np.power(matrixMeanEnergyConsuptions[:,0], 1-w))
	plt.plot(ERWPValues.tolist(), matrixMeanResponseTimes[:,1].tolist(), label="ERWP")
	
def plotMetrics(jsonRawData):
	#matrixMeanEnergyConsuptions = plotMeanEnergyConsuption(jsonRawData)
	matrixMeanResponseTimes = plotMeanResponseTime1(jsonRawData)
	#calcolare ERWP
	"""ERWP = meanEnergyConsuption^(1-w)*meanResponseTime^(1-w) where w is equal to 0.5 by default"""
	#plotERWP(matrixMeanResponseTimes, matrixMeanEnergyConsuptions, w=0.9)
	plt.show()
	


def main(args):
	if (args.exportJson):
		convertVecToJson(args.src, args.dst)
	jsonRawData = listJsonVec(args.dst, args.transiente)
	if args.transiente:
		#checkMean(jsonRawData)
		plotServiceTime(jsonRawData)
	else:
		plotMetrics(jsonRawData)


if __name__== "__main__":
	parser = argparse.ArgumentParser(description='Process vec files.')
	parser.add_argument('--src', help='directory which contains the vecs files')
	parser.add_argument('--dst', help='json destination directory')
	parser.add_argument('--transiente', action='store_true', help='put this parameter in case of transient study')
	parser.add_argument('--exportJson', action='store_true', help='put this parameter in case of json convertion is needed')
	args = parser.parse_args()
	main(args)
