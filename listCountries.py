#! /usr/bin/python3
#
# List all countries mentioned in the COVID-19 data provided by Johns
# Hopkins University
import os
import re
import csv
from estimateR import correctCountryName

dataSourceDir = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"

filesList = []

for root, dirs, files in os.walk(dataSourceDir):
    for file in files:
        if not file.endswith(".csv"):
            continue

        filesList.append(file)

countryList = []
for file in filesList:
    csv_reader = csv.reader(open(dataSourceDir + "/" + file).readlines(), delimiter=",")
    header = next(csv_reader)
    for fields in csv_reader:
        country = fields[3]

        if re.search("[0-9]", fields[3]):
            # country names do not contain numbers
            continue

        if country in ["", "MS Zaandam"]:
            continue

        country = correctCountryName(country)
        countryList.append(country)

countryList = list(set(countryList))
countryList.sort()

for country in countryList:
    if country != "":
        print(country)
