#! /usr/bin/python3

import sys

countryDict = {}

country = sys.argv[1]

f = open("country-populations.csv")
for curLine in f.readlines():
    fields = curLine.split(",")

    countryDict[fields[0]] = float(fields[1])*1000

if country in countryDict:
    print("{}".format(countryDict[country]))
else:
    print("\"\"")
