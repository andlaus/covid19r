#! /bin/bash

IFS="
"

OUTPUT_DIR="processed-data"

mkdir -p "$OUTPUT_DIR"

rm -rf "$OUTPUT_DIR/*"

echo > "$OUTPUT_DIR/countries.csv"

./estimateRAll.py

for COUNTRY in $(./listCountries.py); do
    echo "$COUNTRY,$(./countryPopulation.py $COUNTRY)" >> "$OUTPUT_DIR/countries.csv" 

    mv "$COUNTRY.csv" "$OUTPUT_DIR/"

    echo -n "$COUNTRY: "
    tail -n +1 "$OUTPUT_DIR/$COUNTRY.csv"| wc -l
done
