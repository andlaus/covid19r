#! /usr/bin/python3
#
# this script does the same things as "estimateR.py" except that it
# processes multiple countries at once and writes the result for each
# country into the file $COUNTRY_NAME.csv. Extractiing all ~200
# countries is thus about two orders of magnitude faster.

import estimateR

db = estimateR.createDatabase()

for country in db:
    f = open(f"{country}.csv", "w")
    estimateR.printCountryCsv(db, country, f)
    f.close()
