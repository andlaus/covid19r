#! /bin/bash

IFS="
"

for COUNTRY in $(./listCountries.py | tail -n +2); do
    echo -n "$COUNTRY: "
    ./estimateR.py "$COUNTRY" > "r-estimate-$COUNTRY.csv"
    tail -n +1 "r-estimate-$COUNTRY.csv"| wc -l
done
