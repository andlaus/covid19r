#! /bin/bash

if test "$#" != 1; then
    echo "Usage: $0 COUNTRY_NAME"
    exit 1
fi

COUNTRY="$1"

./estimateR.py "$COUNTRY" > "r-estimate-$COUNTRY.csv"

cat > /tmp/"visualize-R-$COUNTRY.gnuplot" <<EOF

set key autotitle columnhead
set xdata time
set timefmt "%Y-%m-%d"
#set xrange ["2020-04-25":"2020-12-31"]
set format x "%Y/%m/%d"

set yrange [0:2.5]

set title "Curves for $COUNTRY"

plot "r-estimate-$COUNTRY.csv" using 1:6 w lp, "r-estimate-$COUNTRY.csv" using 1:7 w lp

pause -1 "press ENTER to finish"

EOF

gnuplot /tmp/"visualize-R-$COUNTRY.gnuplot"
