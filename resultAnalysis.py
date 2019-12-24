import os
import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
from statistics import mean
import pprint
import scipy.stats as stats


def computeBatchMetrics(data, path510, path712, metric="MRT"):
	assert metric in ["MRT", "MEC", "ERWP"]
 
	print("Computing confidence interval for {}...".format(metric))
 
	numBatch = [5, 7]
	numObs = [10, 12]
	with open(path510, "w+", encoding="UTF-8") as file510, open(path712, "w+", encoding="UTF-8") as file712:
		print("deadline, reneging rate, batch, obs, "+metric+", mean, variance, minVal, maxVal, included", file=file510)
		print("deadline, reneging rate, batch, obs, "+metric+", mean, variance, minVal, maxVal, included", file=file712)
		for deadline, seedsData in data.items():
			values = list(seedsData.values())
			computedValue = np.mean(values)
			#print("Confidence intervals for deadline: {} - {}: {:.3f}".format(deadline, metric, computedValue), file=file)
  
			for batch, obs in zip(numBatch, numObs):
				assert batch * obs <= len(values)
  
			for batch, obs in zip(numBatch, numObs):
				means = np.zeros(batch)
   
				for i in range(batch):
					startIndex = i * obs
					endIndex = (i+1) * obs
					means[i] = np.mean(values[startIndex:endIndex])
   
				generalMean = np.mean(means)
				variance = np.var(means, ddof=1)
				fractionCoeff = np.sqrt(variance/batch)
				minVal, maxVal = stats.t.interval(0.90, batch-1, loc=generalMean, scale=fractionCoeff)
				#print("batch: {}, obs: {}, mean: {:.3f}, variance: {:.3f}, min: {:.3f}, max: {:.3f}{}".format(batch, obs, generalMean, variance, minVal, maxVal, ", OK" if computedValue >= minVal and computedValue <= maxVal else ""), file=file)
				print("{}, {:.3f}, {}, {}, {:.3f}, {:.3f}, {:.3f}, {:.3f}, {:.3f} {}".format(int(int(deadline)/60), 1/(int(int(deadline)/60)), batch, obs, computedValue, generalMean, variance, minVal, maxVal, ", OK" if computedValue >= minVal and computedValue <= maxVal else ""), file= file510 if batch == 5 else file712)
			
			
def convertVecToJson(src, dst):
	for file in os.listdir(src):
		if file.split(".")[-1]=="vec":
			jsonFile = dst + file[:-3]+"json "
			vecFile = src + file
			print (jsonFile)
			os.system("scavetool x -f 'module(\"*\")' -o " + jsonFile + " -F JSON " + vecFile)


def running_avg(x):
    return np.cumsum(x) / np.arange(1, x.size + 1)


def listJsonVec(jsonRoot, transiente):
	filesDict = {}
	for file in os.listdir(jsonRoot):
		with open(jsonRoot + file) as jsonFile:
			tmpJson = json.load(jsonFile)
			firstKey = list(tmpJson.keys())[0]
			seed = tmpJson[firstKey]["itervars"]["seed"]
			deadline = int(tmpJson[firstKey]["itervars"]["deadline"])
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
	

def plotServiceTime(jsonRawData, path=None):
	print("plotServiceTime")
	#switchMode = ["storeWifiTime:vector", "storeCelTime:vector"]
	#deadlineStable = ["storeDeadline:vector"]
	serviceTimes = ["WifiCelNetPassiveQueue.WIFI", "WifiCelNetPassiveQueue.CELL", "WifiCelNetPassiveQueue.LOCAL"]
	for deadline in jsonRawData:
		for metrics in [serviceTimes]:
			for metric in metrics:
				for seed, values in jsonRawData[deadline].items():
					plt.plot(values["serviceTime"][metric][0], running_avg(np.array(values["serviceTime"][metric][1])), label=metric+" "+str(deadline/60))
					#plt.legend()
				if path:
					plt.savefig(path+metric+"_transiente.png")
					plt.close()


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
	mecDict = {}
	for deadline, value in jsonRawData.items():
		mecDict.setdefault(deadline,{})
		#print("deadline: {}".format(deadline))
		meanEnergyConsuptionacc = []
		for seed, val in value.items():
			numWifiJobs = len(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1])
			numCelJobs = len(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1])
			numLocalJobs = len(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1])
			TotalLocalServiceTime = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1])/60 * 2
			TotalWifiServiceTime = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1])/60 * 0.7
			TotalCelServiceTime = np.sum(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1])/60 * 2.5
			print("TotalLocalServiceTime {} TotalWifiServiceTime {} TotalCelServiceTime {}".format(TotalLocalServiceTime,TotalWifiServiceTime,TotalCelServiceTime))
			sumJob = 1#(len(val["serviceTime"]["WifiCelNetPassiveQueue.WIFI"][1])+len(val["serviceTime"]["WifiCelNetPassiveQueue.CELL"][1])+len(val["serviceTime"]["WifiCelNetPassiveQueue.LOCAL"][1]))
			#meanEnergyConsuptionacc.append(1 / (1/120) * np.sum([TotalConsuptionWifi, TotalConsuptionCel, TotalConsuptionLocal]) / sumJob)
			#mec = ((TotalWifiServiceTime)*0.7/numWifiJobs+(TotalCelServiceTime)*2.5/numCelJobs+(TotalLocalServiceTime)*2/numLocalJobs)/sumJob
			mec = (TotalLocalServiceTime+TotalWifiServiceTime+TotalCelServiceTime) / (numWifiJobs+numCelJobs+numLocalJobs)
			meanEnergyConsuptionacc.append(mec)
			mecDict[deadline].setdefault(seed, mec)
		meanEnergyConsuptions.append(np.mean(meanEnergyConsuptionacc))
		deadlines.append(deadline/60)
	matrixMeanEnergyConsuptions = np.column_stack((deadlines, meanEnergyConsuptions))
	matrixMeanEnergyConsuptions = matrixMeanEnergyConsuptions[matrixMeanEnergyConsuptions[:,0].argsort()]
	return matrixMeanEnergyConsuptions, mecDict
	
def plotMeanResponseTime1(jsonRawData):
	deadlines = []
	meanResponseTimes = []
	mrtDict = {}
	#seed = 7
	# non avendo distinzione tra coda wifi e coda cellulate suppongo che la coda offload sia una buona indicazione media di entrambe, quindi la considero come un'unica metrica 
	for deadline, value in jsonRawData.items():
		mrtDict.setdefault(deadline, {})
		meanResponseTimeacc = []
		for seed, val in value.items():
			TotallifeTimeActiveTime = np.mean(val["lifeTime"]["lifeTime:vector"][1])
			meanResponseTimeacc.append(TotallifeTimeActiveTime)
			mrtDict[deadline].setdefault(seed, TotallifeTimeActiveTime)
		tempMean = np.mean(meanResponseTimeacc)/60
		meanResponseTimes.append(tempMean)
		deadlines.append(deadline/60)
	matrixMeanResponseTimes = np.column_stack((deadlines, meanResponseTimes))
	matrixMeanResponseTimes = matrixMeanResponseTimes[matrixMeanResponseTimes[:,0].argsort()]
	return matrixMeanResponseTimes, mrtDict


def plotMeanResponseTime(jsonRawData):
	deadlines = []
	meanResponseTimes = []
	TotalLocalActiveTime = 1
	for deadline, value in jsonRawData.items():
		meanResponseTimeacc = []
		for seed, val in value.items():
			TotalWifiActiveTime = 1#np.sum(val["serviceTime"]["storeWifiTime:vector"][1])
			TotalCelActiveTime = 1#np.sum(val["serviceTime"]["storeCelTime:vector"][1])
			meanResponseTimeacc.append((np.sum([np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.WIFI"][1])/TotalWifiActiveTime, np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.CELL"][1])/TotalCelActiveTime, np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.REMOTE"][1])/TotalLocalActiveTime, np.mean(value[seed]["responseTime"]["WifiCelNetPassiveQueue.LOCAL"][1])/TotalLocalActiveTime]))/60)
		meanResponseTimes.append(np.mean(meanResponseTimeacc)/60)
		deadlines.append(deadline/60)
	matrixMeanResponseTimes = np.column_stack((deadlines, meanResponseTimes))
	matrixMeanResponseTimes = matrixMeanResponseTimes[matrixMeanResponseTimes[:,0].argsort()]
	return matrixMeanResponseTimes

def genERWPDict(mrtDict, mecDict, ws=[0.5]):
	ERWPDict = {}
	for w in ws:
		ERWPDict.setdefault(w, {})
		for deadline, values in mrtDict.items():
			ERWPDict[w].setdefault(deadline, {})
			for seed, val in mrtDict[deadline].items():
				ERWP = (val**(1-w)) * (mecDict[deadline][seed]**(w))
				ERWPDict[w][deadline].setdefault(seed, ERWP)
	return ERWPDict


def plotEnergyRWP(matrixMeanResponseTimes, matrixMeanEnergyConsuptions, ws=[0.5], path=None):
	for w in ws:
		ERWPValues = np.multiply(np.power(matrixMeanResponseTimes[:,1], 1-w), np.power(matrixMeanEnergyConsuptions[:,1], w))
		plt.plot((1/matrixMeanResponseTimes[:,0]).tolist(), ERWPValues.tolist(), label="exponent "+str(w))
		plt.legend()
	if path:
		plt.savefig(path+"_"+str(w)+".png")
		plt.close()
		#chargePlot(ERWPValues)
	
	
def chargePlot(matrix, path=None):
	xs = matrix[:,0]
	ys = matrix[:,1]
	plt.plot(xs.tolist(), ys.tolist())
	coeff = np.polyfit(xs.flatten(), ys.flatten(), 5)
	p = np.poly1d(coeff)
	plt.plot(xs.tolist(), p(xs).tolist())
	if path:
		plt.savefig(path)
		plt.close()
	
def plotMetrics(jsonRawData, plotMRT=False, plotMEC=False, plotERWP=False, path=None):
	
	matrixMeanResponseTimes, mrtDict = plotMeanResponseTime1(jsonRawData)
	matrixMeanEnergyConsuptions, mecDict = plotMeanEnergyConsuption(jsonRawData)
	#plotERWP(matrixMeanResponseTimes=matrixMeanResponseTimes, matrixMeanEnergyConsuptions=matrixMeanEnergyConsuptions)
	if plotMRT:
		chargePlot(matrixMeanResponseTimes, path+"mrtPlot.png")
	if plotMEC:
		chargePlot(matrixMeanEnergyConsuptions, path+"mecPlot.png")
	if plotERWP:
		plotEnergyRWP(matrixMeanResponseTimes, matrixMeanEnergyConsuptions, ws=[0.1, 0.5, 0.9], path=path+"ERWPPlot")
	return matrixMeanResponseTimes, matrixMeanEnergyConsuptions, mecDict, mrtDict


def main(args):
	ROOT = "./resultAnalysis/"
	RESULTSOUT = ROOT+args.outSimDir+"/"
	RESOULTSIMAGES = ROOT+"images/"+args.outSimDir+"/"
	os.makedirs(RESULTSOUT, exist_ok=True)
	os.makedirs(RESOULTSIMAGES, exist_ok=True)
	if (args.exportJson):
		convertVecToJson(args.src, args.dst)
	jsonRawData = listJsonVec(args.dst, args.transiente)
	if args.transiente:
		plotServiceTime(jsonRawData, RESOULTSIMAGES)
	else:
		matrixMeanResponseTimes, matrixMeanEnergyConsuptions, mecDict, mrtDict = plotMetrics(jsonRawData, args.plotMRT, args.plotMEC, args.plotERWP, path=RESOULTSIMAGES)
		#plt.show()
		if args.plotERWP:
			ws = [0.1, 0.5, 0.9]
			ERWPDict = genERWPDict(mrtDict=mrtDict, mecDict=mecDict, ws=ws)
		computeBatchMetrics(mecDict, RESULTSOUT+"5-10_mecIntervals.csv", RESULTSOUT+"7-12_mecIntervals.csv","MEC")
		computeBatchMetrics(mrtDict, RESULTSOUT+"5-10_mrtIntervals.csv", RESULTSOUT+"7-12_mrtIntervals.csv", "MRT")
		for w, values in  ERWPDict.items():
			computeBatchMetrics(values, RESULTSOUT+"5-10_ERWPIntervals"+str(w)+".csv",RESULTSOUT+"7-12_ERWPIntervals"+str(w)+".csv","ERWP")

if __name__== "__main__":
	parser = argparse.ArgumentParser(description='Process vec files.')
	parser.add_argument('--src', help='directory which contains the vecs files')
	parser.add_argument('--dst', help='json destination directory')
	parser.add_argument('--transiente', action='store_true', help='put this parameter in case of transient study')
	parser.add_argument('--exportJson', action='store_true', help='put this parameter in case of json convertion is needed')
	parser.add_argument('--plotMRT', action='store_true', help='put this parameter if you want to print MRT')
	parser.add_argument('--plotMEC', action='store_true', help='put this parameter if you want to print MEC')
	parser.add_argument('--plotERWP', action='store_true', help='put this parameter if you want to print ERWP')
	parser.add_argument('--outSimDir', help='inster the name of the Simulation')

	args = parser.parse_args()
	main(args)
