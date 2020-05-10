#! /usr/bin/python3
import os
import sys
import datetime
import operator as op
from functools import reduce

country = "Germany"
if len(sys.argv) > 1:
    country = sys.argv[1]

def nChosek(n, k):
    k = min(k, n-k)
    numer = reduce(op.mul, range(n, n-k, -1), 1)
    denom = reduce(op.mul, range(1, k+1), 1)
    return numer / denom

# generate a binomially distributed kernel to distribute the new cases
# of a given day over the past and the future. be aware that this is
# basically handwaveing and I have no data whatsoever to back it
# up. IMO the curves look plausible, though.
numDaysInfectious = 10 # number of days a case has an effect on the
                       # number of reported cases
weightsOffset = -4 # first day a case has an influence on the reported
                   # numbers [days after an infection is reported]
k = 7 # specify the "center of infectiousness" of new cases w.r.t. the
      # report date. we set this slightly to the future, i.e., larger
      # than the negative weightsOffset [range: [0, 10]]

weightsList = []
sumWeights = 0.0
for i in range(0, numDaysInfectious + 1):
    p = i / float(numDaysInfectious)

    # use the binomial distribution. This is not based on any evidence
    # except for "looks reasonable to me"!
    weightsList.append(nChosek(numDaysInfectious, k) * p**k * (1 - p)**(numDaysInfectious - k))
    sumWeights += weightsList[-1]

# normalize the weights list
weightsList = list(map(lambda x: x/sumWeights, weightsList))

def boxFilter(data, n):
    result = []

    for i in range(0, len(data)):
        sumValues = 0
        numValues = 0
        for j in range(max(0, int(i - n)), min(len(data), int(i + 1))):
            numValues += 1
            sumValues += data[j]

        result.append(sumValues/numValues)

    return result

dataSourceDir = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"

filesList = []

for root, dirs, files in os.walk(dataSourceDir):
    for file in files:
        if not file.endswith(".csv"):
            continue

        filesList.append(file)

def fileNameToDateTime(fileName):
    dt = datetime.datetime.strptime(fileName, '%m-%d-%Y.csv')
    return dt
filesList.sort(key=fileNameToDateTime)

timeList = []
totalCases = []
deltaCases = []
for file in filesList:
    for curLine in open(dataSourceDir + "/" + file).readlines():
        fields = curLine.split(",")
        numCases = None
        if fields[3] == country and fields[2] == "":
            numCases = int(fields[7])
        elif country == "US":
            # as usual, things are done differently in the US: we need
            # to sum the number of cases for every ZIP code in the
            # file. Also, some data points like Cruise ships do not
            # have ZIP codes (we do not consider them for now)
            if fields[3] == country and fields[0] != "":
                numCases = int(fields[7])
            elif fields[1] == country:
                # before March 22, US data is state based, not zipcode
                # based
                numCases = int(fields[3])
            else:
                continue
        elif fields[1] == country and (fields[0] == "" or fields[0] == country):
            # the format of the data changed at some point in
            # march. we can also make use the old format...
            numCases = int(fields[3])
        else:
            # line not applicable
            continue

        dt = fileNameToDateTime(file)

        if len(timeList) == 0 or timeList[-1] != dt:
            timeList.append(dt)
            totalCases.append(0)

        totalCases[-1] += numCases

# compute the number of daily new cases based on the total cases
for i, numCases in enumerate(totalCases):
    if i > 1:
        # some countries like Spain report a negative number of
        # new cases on some days, probably due to discovering
        # errors in data collection (e.g., cases counted multiple
        # times, etc.). while this is in general not a felony, it
        # spoils our curves too much, so we don't allow negative
        # new case numbers...
        deltaCases.append(max(0, numCases - totalCases[i - 1]))
    else:
        deltaCases.append(numCases)

deltaCasesConv = boxFilter(deltaCases, n=7)
totalCasesConv = boxFilter(totalCases, n=7)

# compute the attributable weight based on the filtered case deltas
attributableWeight = [0.0]*len(timeList)
for i in range(0, len(timeList)):
    # the new cases seen at day i are the ones which we need to
    # distribute amongst day i's neighbors using the weightList array
    for j, w in enumerate(weightsList):
        dayIdx = i + weightsOffset + j
        if dayIdx < 0:
            continue
        elif dayIdx + 1 > len(timeList):
            continue

        attributableWeight[dayIdx] += w * deltaCasesConv[i]

# the estimated R factor of a given day simply is the ratio between
# number of observed cases and the attributable weight of that day.
estimatedR = []
for i, n in enumerate(deltaCasesConv):
    R = 3.0
    if totalCasesConv[i] >= 100 and attributableWeight[i] > 1e-10:
        R = n/attributableWeight[i]

    estimatedR.append(R)

# print the results
print('Date "Total Cases" "New Cases" "Smoothened Total Cases" "Smoothened New Cases" "R Estimate"')
for i in range(0, len(timeList)):
    print("{} {} {} {} {} {}".format(timeList[i].strftime("%Y-%m-%d"),
                                     totalCases[i],
                                     deltaCases[i],
                                     totalCasesConv[i],
                                     deltaCasesConv[i],
                                     estimatedR[i]))
