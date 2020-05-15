#! /bin/bash

IFS="
"

OUTPUT_DIR="processed-data"

mkdir -p "$OUTPUT_DIR"

echo > "$OUTPUT_DIR/countries.csv"

for COUNTRY in $(./listCountries.py | tail -n +2); do
    echo -n "$COUNTRY: "
    echo "$COUNTRY" >> "$OUTPUT_DIR/countries.csv" 
    ./estimateR.py "$COUNTRY" > "$OUTPUT_DIR/$COUNTRY.csv"
    tail -n +1 "$OUTPUT_DIR/$COUNTRY.csv"| wc -l
done
