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

def boxFilter(timeList, data, n, offset=0):
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

def createDatabase():
    def applyErrata(db):
        """Apply some errata to the raw data.

        The intention is to e.g. smoothen big retrospecive corrections
        of a country's data to fix obviously errors in the curves.
        """
        usEntry = db["United States of America"]

        # the data for the US is strange on 28-01-2021. We interpolate
        # the totals between the days before and after.
        i = usEntry["timeList"].index(datetime.datetime(2021, 1, 28))
        a = usEntry["totalCases"][i-1]
        b = usEntry["totalCases"][i+1]
        usEntry["totalCases"][i] = (a+b)/2

        a = usEntry["totalDeaths"][i-1]
        b = usEntry["totalDeaths"][i+1]
        usEntry["totalDeaths"][i] = (a+b)/2
    
    db = {}

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

            curLine = curLine.replace("Iran (Islamic Republic of)", "Iran")
            curLine = curLine.replace("occupied Palestinian territory", "West Bank and Gaza")
            curLine = curLine.replace("Palestine", "West Bank and Gaza")
            curLine = curLine.replace("Republic of Ireland", "Ireland")
            curLine = curLine.replace("Republic of Moldova", "Moldova")
            curLine = curLine.replace("Republic of Congo", "Congo (Brazzaville)")
            curLine = curLine.replace("Republic of the Congo", "Congo (Brazzaville)")
            curLine = curLine.replace("Czech Republic", "Czechia")    
            curLine = curLine.replace("East Timor", "Timor-Leste")
            curLine = curLine.replace(" Azerbaijan", "Azerbaijan")
            curLine = curLine.replace(" Afghanistan", "Afghanistan")
            curLine = curLine.replace("Cape Verde", "Cabo Verde")
            curLine = curLine.replace("Vatican City", "Holy See")
            curLine = curLine.replace("Viet Nam", "Vietnam")
            curLine = curLine.replace("UK", "United Kingdom")
            curLine = curLine.replace("The Gambia", "Gambia")
            curLine = curLine.replace("The Bahamas", "Bahamas")
            curLine = curLine.replace("Taipei and environs", "Taiwan")
            curLine = curLine.replace("Russian Federation", "Russia")
            curLine = curLine.replace("Ivory Coast", "Cote d'Ivoire")
            
            curLine = curLine.replace('Mainland China', "China")
            curLine = curLine.replace("Hong Kong SAR", "China")
            curLine = curLine.replace("Hong Kong", "China")
            curLine = curLine.replace("Macao SAR", "China")
            curLine = curLine.replace("Macau", "China")

            curLine = curLine.replace("US", "United States of America")
            curLine = curLine.replace("Puerto Rico", "United States of America")
            curLine = curLine.replace("Guam", "United States of America")

            curLine = curLine.replace("North Ireland", "United Kingdom")
            curLine = curLine.replace("Gibraltar", "United Kingdom")
            curLine = curLine.replace("Cayman Islands", "United Kingdom")
            curLine = curLine.replace("Channel Islands", "United Kingdom")
            curLine = curLine.replace("Jersey", "United Kingdom")
            curLine = curLine.replace("Guernsey", "United Kingdom")

            curLine = curLine.replace("Martinique", "France")
            curLine = curLine.replace("Guadeloupe", "France")
            curLine = curLine.replace("French Guiana", "France")    
            curLine = curLine.replace("St. Martin", "France")
            curLine = curLine.replace("Saint Martin", "France")
            curLine = curLine.replace("Saint Barthelemy", "France")
            curLine = curLine.replace("Reunion", "France")
            curLine = curLine.replace("Mayotte", "France")

            curLine = curLine.replace("Greenland", "Denmark")    
            curLine = curLine.replace("Faroe Islands", "Denmark")    

            curLine = curLine.replace("Aruba", "Netherlands")
            curLine = curLine.replace("Curacao", "Netherlands")

            curLine = re.sub("\"[a-zA-Z0-9,(). ]*\",", ",", curLine) # US City names screw things up with commas in their names

            fields = curLine.split(",")

            numCases = 0
            numDeaths = 0
            if dt < format1Date:
                if fields[0] == "Cruise Ship":
                    country = "Diamond Princess"
                elif fields[0] == "Grand Princess Cruise Ship":
                    continue # the "grand princess cruise ship" data seems to be attributed to the US, we don't want that
                elif fields[1] == "Cruise Ship":
                    country = fields[0]
                else:
                    country = fields[1]
                if fields[3] != "":
                    numCases = int(fields[3])
                if fields[4] != "":
                    numDeaths = int(fields[4])
            else:
                country = fields[3]
                if fields[7] != "":
                    numCases = int(fields[7])
                if fields[8] != "":
                    numDeaths = int(fields[8])

            country = country.replace("Cruise Ship", "Diamond Princess")

            if country in ["Others", "MS Zaandam"]:
                continue


            if country not in db:
                db[country] = {
                    "timeList": [],
                    "totalCases": [],
                    "totalDeaths": [],
                }
            
            if len(db[country]["timeList"]) == 0 or db[country]["timeList"][-1] != dt:
                db[country]["timeList"].append(dt)
                db[country]["totalCases"].append(0)
                db[country]["totalDeaths"].append(0)

            db[country]["totalCases"][-1] += numCases
            db[country]["totalDeaths"][-1] += numDeaths

    applyErrata(db)
            
    for country in db:
        # the number of daily new cases based on the total cases
        db[country]["deltaCases"] = []
        # the number of daily deaths based on the total deaths
        db[country]["deltaDeaths"] = []
        # number of deaths divided by 0.017 (the lethality on the Diamond
        # Princess cruise ship)
        db[country]["totalCases2"] = []
        for i, numCases in enumerate(db[country]["totalCases"]):
            if i > 1:
                # some countries like Spain report a negative number of
                # new cases on some days, probably due to discovering
                # errors in data collection (e.g., cases counted multiple
                # times, etc.). while this is in general not a felony, it
                # spoils our curves too much, so we don't allow negative
                # new case numbers...
                db[country]["deltaCases"].append(max(0, db[country]["totalCases"][i] - db[country]["totalCases"][i - 1]))
                db[country]["deltaDeaths"].append(max(0, db[country]["totalDeaths"][i] - db[country]["totalDeaths"][i - 1]))
            else:
                db[country]["deltaCases"].append(numCases)
                db[country]["deltaDeaths"].append(db[country]["totalDeaths"][i])

            # death is delayed relative to infection for about three weeks and
            # relative to confirmation for about 14 days...
            if i >= 14:
                db[country]["totalCases2"].append(db[country]["totalDeaths"][i] * (712./13))

        # compute the attributable weight based on the filtered case deltas
        db[country]["attributableWeight"] = [0.0]*len(db[country]["timeList"])
        for i in range(0, len(db[country]["timeList"])):
            # the new cases seen at day i are the ones which we need to
            # distribute amongst day i's neighbors using the weightList array
            for j, w in enumerate(weightsList):
                dayIdx = i + weightsOffset + j
                if dayIdx < 0:
                    continue
                elif dayIdx + 1 > len(db[country]["timeList"]):
                    continue

                db[country]["attributableWeight"][dayIdx] += w * db[country]["deltaCases"][i]

        # the estimated R factor of a given day simply is the ratio between
        # number of observed cases and the attributable weight of that day.
        db[country]["estimatedR"] = []
        for i, n in enumerate(db[country]["deltaCases"]):
            R = None
            if db[country]["totalCases"][i] >= 100 and db[country]["attributableWeight"][i] > 1e-10:
                R = db[country]["deltaCases"][i]/db[country]["attributableWeight"][i]

            db[country]["estimatedR"].append(R)

        db[country]["totalCasesSmoothened"] = boxFilter(db[country]["timeList"], db[country]["totalCases"], n=7)
        db[country]["totalCases2Smoothened"] = boxFilter(db[country]["timeList"], db[country]["totalCases2"], n=7)
        db[country]["deltaCasesSmoothened"] = boxFilter(db[country]["timeList"], db[country]["deltaCases"], n=7)
        db[country]["totalDeathsSmoothened"] = boxFilter(db[country]["timeList"], db[country]["totalDeaths"], 7)
        db[country]["deltaDeathsSmoothened"] = boxFilter(db[country]["timeList"], db[country]["deltaDeaths"], 7)
        db[country]["estimatedRSmoothened"] = boxFilter(db[country]["timeList"], db[country]["estimatedR"], 7)

    return db

def printCountryCsv(db, country, outFile):
    if country not in db:
        return

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
          '"Smoothened \'Diamond Princess Total Case Estimate\'" ',
          file=outFile)
    for i in range(0, len(db[country]["timeList"])):
        tc2 =  "\"\""
        tc2s = "\"\""
        if i < len(db[country]["totalCases2"]):
            tc2 = db[country]["totalCases2"][i]
            tc2s = db[country]["totalCases2Smoothened"][i]

        R = "\"\"" if db[country]["estimatedR"][i] is None else db[country]["estimatedR"][i]
        Rs = "\"\"" if db[country]["estimatedRSmoothened"][i] is None else db[country]["estimatedRSmoothened"][i]
        print(f'{db[country]["timeList"][i].strftime("%Y-%m-%d")}' + \
              f' {db[country]["totalCases"][i]}'+ \
              f' {db[country]["deltaCases"][i]}'+ \
              f' {db[country]["totalDeaths"][i]}'+ \
              f' {db[country]["deltaDeaths"][i]}'+ \
              f' {R}'+ \
              f' {tc2}'+ \
              f' {db[country]["totalCasesSmoothened"][i]}'+ \
              f' {db[country]["deltaCasesSmoothened"][i]}'+ \
              f' {db[country]["totalDeaths"][i]}'+ \
              f' {db[country]["deltaDeaths"][i]}'+ \
              f' {Rs}'+ \
              f' {tc2s}', file=outFile)
        
if __name__ == "__main__":
    country = "Germany"
    if len(sys.argv) > 1:
        country = sys.argv[1]
    
    db = createDatabase()

    printCountryCsv(db, country, sys.stdout)
    
