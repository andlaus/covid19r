## COVID-19 Basic Reproduction Factor Estimator

This Repository contains a small python script to estimate the basic
reproduction number R of SARS-CoV 2 (the virus causing COVID-19) for
various countries over time.

## Usage

This project assumes that you are using a non-ancient Linux
distribution which has [Python3](https://python.org) and
[git](https://git-scm.com) installed. If you want to visualize the
results, having [gnuplot](http://www.gnuplot.info) also installed is
highly advised.

First, you need to clone (or if you already run the script, update)
the input data from [Johns Hopkins University](https://github.com/CSSEGISandData/COVID-19):

```
./updateData.sh
```

After this, you can extract the Data of most countries like this

```
COUNTRY="Germany"
./estimateR.py "$COUNTRY" > "r-estimate-$COUNTRY.csv"
```

You can then visualize the result using `gnuplot`. To simplify this,
another shell script is provided:

```
COUNTRY="Germany"
./estimateAndVisualizeR.sh "$COUNTRY"
```
