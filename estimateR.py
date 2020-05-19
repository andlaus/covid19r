#! /usr/bin/python3
#
# This script computes an estimate of the "reverse" basic reproduction
# number R of SARS CoV 2 for a country.
#
# Notes/Caveats:
#
# - "Reverse R" means that it is an estimate of the past reproduction
#   number of infectious cases that are needed to cause the cases seen at
#   a given day.
# - The approach taken by this script is not scientifically validated,
#   although it looks quite reasonable to me:
#   - We assume that the probability that somebody infects someone else
#     who is reported follows a binomial distribution which is slightly
#     skewed towards the future.
#   - Due to the way this is implemented, the numbers for the last three
#     days will thus slightly decrease once new data becomes available! The
#     rationale for this is that cases reported on a given day could have
#     caused some of the cases reported on earlier days.
#   - An "infectious case" is an active case that has not been
#     recognized. Once a case has been discovered, we assume that this
#     person gets quarantined and will not infect others anymore. It will
#     still affect the reported numbers of the following days due to
#     diagnostic and reporting delays, though.
#   - To reduce statistical noise, the curve is smoothened using a 7
#     day running average. The reason for this is that the data of all
#     countries seems to exhibit a fair amount of statistical noise
#     and almost all countries show strong oscilations with a weekly cycle
#     ("weekend effect"). Both the raw and the smoothened
#     estimates of reverse R are included in the result data.
# - The curves produced here can be at most as good as the input data
#   for a given country. In particular, this means that they might be
#   quite significantly off if the respective country's data
#   aquisition system and/or testing system get overwhelmed or on days
#   around where the reporting methodology gets changed.
# - We assume that all infectious cases will be reported
#   eventually. This is certainly not the case, but as long as the
#   ratio of undiscovered to total cases remains constant (it probably
#   doesn't, see previous bullet point), this should not matter.
# - For small numbers, the R factor is subject to noise and not very
#   significant in the first place. For example this happens for
#   Taiwan.
#
# TODO/IDEAS:
#
# - Add an estimate of the confidence intervals. This involves getting
#   a grip on the quality of the input data as well as considering the
#   total number of cases.
# - Add a "political advice" system: Given a level of acceptable risk,
#   produce a number of whether loosening or tightening restrictions
#   is advisable. Besides the user input of the allowable risk level
#   and the estimate of R, this involves considering the total active
#   case numbers per capita, the confidence intervall of the estimate
#   as well as the reporting delay. Only producing this on a weekly
#   basis would be a bonus.
# - To reduce the impact of unreported cases, check if the number of
#   reported deaths is a better proxy for the number of total
#   cases. The main problems here are that this data is even more
#   delayed than the number of confirmed cases and that it seems to be
#   even noisier and may be more affected by external factors such as age
#   distribution of the cases.
import os
import sys
import re
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
numDaysInfectious = 16 # number of days a case has an effect on the
                       # number of reported cases
weightsOffset = -10 # first day a case has an influence on the reported
                   # numbers [days after an infection is reported]
k = 12 # specify the "center of infectiousness" of new cases w.r.t. the
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

def boxFilter(data, n, offset=0):
    result = []

    # TODO: the data may have gaps or redundancies, i.e., dates where
    # no data point or multiple data points are available. So far we
    # just detect and warn about this...

    hasGaps = False
    for i in range(0, len(data)):
        sumValues = 0
        numValues = 0

        j0 = max(0, int(i - n + 1 + offset))
        j1 = min(len(data), int(i + offset) + 1)
        for j in range(j0, j1):
            if data[j] is None:
                hasGaps = True
                continue

            numValues += 1
            sumValues += data[j]

        dt = timeList[j1 - 1] - timeList[j0]
        hasGaps = hasGaps or (dt.days + 1 != numValues)

        if numValues > 0:
            result.append(sumValues/numValues)
        else:
            result.append(None)

#    if hasGaps:
#        print("Warning: Input data seems to have gaps or multiples", file=sys.stderr)

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
totalDeaths = []

format1Date = datetime.datetime(2020, 3, 22)

for fileName in filesList:
    dt = fileNameToDateTime(fileName)
    for i, curLine in enumerate(open(dataSourceDir + "/" + fileName).readlines()):
        # skip first line (headlines)
        if i == 0:
            continue

        # some countries have weird names and are not unique over
        # time, rectify this
        curLine = curLine.replace('"Korea, South"', "South Korea")
        curLine = curLine.replace('Republic of Korea', "South Korea")
        curLine = curLine.replace('Taiwan*', "Taiwan")
        curLine = curLine.replace('Mainland China', "China")
        curLine = re.sub("\"[a-zA-Z0-9,(). ]*\",", ",", curLine) # US City names screw things up with commas in their names

        fields = curLine.split(",")

        numCases = 0
        numDeaths = 0
        if dt < format1Date:
            if fields[0] == "Cruise Ship":
                countryLine = "Diamond Princess"
            elif fields[0] == "Grand Princess Cruise Ship":
                continue # the "grand princess cruise ship" data seems to be attributed to the US, we don't want that
            elif fields[1] == "Cruise Ship":
                countryLine = fields[0]
            else:
                countryLine = fields[1]
            if fields[3] != "":
                numCases = int(fields[3])
            if fields[4] != "":
                numDeaths = int(fields[4])
        else:
            countryLine = fields[3]
            if fields[7] != "":
                numCases = int(fields[7])
            if fields[8] != "":
                numDeaths = int(fields[8])

        countryLine = countryLine.replace("US", "United States of America")

        if countryLine != country:
            continue


        if len(timeList) == 0 or timeList[-1] != dt:
            timeList.append(dt)
            totalCases.append(0)
            totalDeaths.append(0)

        totalCases[-1] += numCases
        totalDeaths[-1] += numDeaths

# the number of daily new cases based on the total cases
deltaCases = []
# the number of daily deaths based on the total deaths
deltaDeaths = []
# number of deaths divided by 0.017 (the lethality on the Diamond
# Princess cruise ship)
totalCases2 = []
for i, numCases in enumerate(totalCases):
    if i > 1:
        # some countries like Spain report a negative number of
        # new cases on some days, probably due to discovering
        # errors in data collection (e.g., cases counted multiple
        # times, etc.). while this is in general not a felony, it
        # spoils our curves too much, so we don't allow negative
        # new case numbers...
        deltaCases.append(max(0, totalCases[i] - totalCases[i - 1]))
        deltaDeaths.append(max(0, totalDeaths[i] - totalDeaths[i - 1]))
    else:
        deltaCases.append(numCases)
        deltaDeaths.append(totalDeaths[i])

    # death is delayed relative to infection for about three weeks and
    # relative to confirmation for about 14 days...
    if i >= 14:
        totalCases2.append(totalDeaths[i] * (712./13))

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

        attributableWeight[dayIdx] += w * deltaCases[i]

# the estimated R factor of a given day simply is the ratio between
# number of observed cases and the attributable weight of that day.
estimatedR = []
for i, n in enumerate(deltaCases):
    R = None
    if totalCases[i] >= 100 and attributableWeight[i] > 1e-10:
        R = deltaCases[i]/attributableWeight[i]

    estimatedR.append(R)

totalCasesSmoothened = boxFilter(totalCases, n=7)
totalCases2Smoothened = boxFilter(totalCases2, n=7)
deltaCasesSmoothened = boxFilter(deltaCases, n=7)
totalDeathsSmoothened = boxFilter(totalDeaths, 7)
deltaDeathsSmoothened = boxFilter(deltaDeaths, 7)
estimatedRSmoothened = boxFilter(estimatedR, 7)

# print the results
print('Date '+ \
      '"Total Cases" '+ \
      '"New Cases" '+ \
      '"Total Deaths" '+ \
      '"New Deaths" '+ \
      '"Estimated R" '+ \
      '"\'Diamond Princess Total Case Estimate\'" '+ \
      '"Smoothened Total Cases" '+ \
      '"Smoothened New Cases" '+ \
      '"Smoothened Total Deaths" '+ \
      '"Smoothened New Deaths" '+ \
      '"Smoothened Estimated R" '+ \
      '"Smoothened \'Diamond Princess Total Case Estimate\'" ')
for i in range(0, len(timeList)):
    tc2 =  "\"\""
    tc2s = "\"\""
    if i < len(totalCases2):
        tc2 = totalCases2[i]
        tc2s = totalCases2Smoothened[i]

    R = "\"\"" if estimatedR[i] is None else estimatedR[i]
    Rs = "\"\"" if estimatedRSmoothened[i] is None else estimatedRSmoothened[i]
    formatString = "{date} " + \
        "{totalCases} "+ \
        "{newCases} "+ \
        "{totalDeaths} "+ \
        "{newDeaths} "+ \
        "{estimatedR} "+ \
        "{dpTotalCasesEstimate} "+ \
        "{smoothenedTotalCases} "+ \
        "{smoothenedNewCases} "+ \
        "{smoothenedTotalDeaths} "+ \
        "{smoothenedNewDeaths} "+ \
        "{smoothenedEstimatedR} "+ \
        "{smoothenedDpTotalCasesEstimate} "
    print(formatString.format(**{
        "date": timeList[i].strftime("%Y-%m-%d"),
        "totalCases":totalCases[i],
        "newCases":deltaCases[i],
        "totalDeaths":totalDeaths[i],
        "newDeaths":deltaDeaths[i],
        "estimatedR":R,
        "dpTotalCasesEstimate":tc2,
        "smoothenedTotalCases":totalCasesSmoothened[i],
        "smoothenedNewCases":deltaCasesSmoothened[i],
        "smoothenedTotalDeaths":totalDeaths[i],
        "smoothenedNewDeaths":deltaDeaths[i],
        "smoothenedEstimatedR":Rs,
        "smoothenedDpTotalCasesEstimate":tc2s,
    }))
