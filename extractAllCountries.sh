#! /bin/bash

IFS="
"

OUTPUT_DIR="processed-data"

mkdir -p "$OUTPUT_DIR"

echo > "$OUTPUT_DIR/countries.csv"

./estimateRAll.py

for BLA in $(ls *.csv | grep -v country-populations); do
    mv "$BLA" "$OUTPUT_DIR"
done

for COUNTRY in $(./listCountries.py | tail -n +2); do
    echo "$COUNTRY,$(./countryPopulation.py $COUNTRY)" >> "$OUTPUT_DIR/countries.csv" 
    echo -n "$COUNTRY: "
    tail -n +1 "$OUTPUT_DIR/$COUNTRY.csv"| wc -l
done
