#! /usr/bin/python3
#
# List all countries mentioned in the COVID-19 data provided by Johns
# Hopkins University
import os
import re

dataSourceDir = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"

filesList = []

for root, dirs, files in os.walk(dataSourceDir):
    for file in files:
        if not file.endswith(".csv"):
            continue

        filesList.append(file)

countryList = []
for file in filesList:
    for curLine in open(dataSourceDir + "/" + file).readlines():
        # some countries have weird names and are not unique over
        # time, rectify this
        curLine = curLine.replace('"Korea, South"', "South Korea")
        curLine = curLine.replace('"Bonaire, Sint Eustatius and Saba"', 'Bonaire; Sint Eustatius and Saba')
        curLine = curLine.replace('Taiwan*', "Taiwan")

        fields = curLine.split(",")
        country = None
        if fields[3] != "":
            if re.search("[0-9]", fields[3]):
                # country names do not contain numbers
                continue

            country = fields[3]
        else:
            # line not applicable
            continue

        if country in ("Cruise Ship", "MS Zaandam", "Confirmed", "Country_Region"):
            continue

        country = country.replace("US", "United States of America")
        
        countryList.append(country)

countryList = list(set(countryList))
countryList.sort()

for country in countryList:
    if country != "":
        print(country)
