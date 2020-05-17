#! /bin/bash

if test "$#" -lt 1; then
    echo "Usage: $0 COUNTRY_NAME [FIELDS_TO_PLOT]"
    exit 1
fi

COUNTRY="$1"

FIELDS="6 12"
RANGE="set yrange [:2.5];"
if test "$#" -gt 1; then
    FIELDS="${@:2}"
    RANGE=""
    echo "Using custom fields: $FIELDS"
fi

OUTPUT_DIR="processed-data"

mkdir -p "$OUTPUT_DIR"

./estimateR.py "$COUNTRY" > "$OUTPUT_DIR/$COUNTRY.csv"

cat > /tmp/"visualize-R-$COUNTRY.gnuplot" <<EOF

set key autotitle columnhead
set xdata time
set timefmt "%Y-%m-%d"
#set xrange ["2020-04-25":"2020-12-31"]
set format x "%Y/%m/%d"

$RANGE

set title "Curves for $COUNTRY"
EOF

echo -n "plot " >> /tmp/"visualize-R-$COUNTRY.gnuplot"

for FIELD in $FIELDS; do
    echo -n "\"$OUTPUT_DIR/$COUNTRY.csv\" using 1:$FIELD w lp, " >> /tmp/"visualize-R-$COUNTRY.gnuplot"
done

echo >> /tmp/"visualize-R-$COUNTRY.gnuplot"
echo >> /tmp/"visualize-R-$COUNTRY.gnuplot"

echo "pause -1 \"press ENTER to finish\"" >> /tmp/"visualize-R-$COUNTRY.gnuplot"


gnuplot /tmp/"visualize-R-$COUNTRY.gnuplot"
