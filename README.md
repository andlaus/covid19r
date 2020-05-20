# COVID-19 Basic Reproduction Factor Estimator

This Repository contains a small python script to estimate the basic
reproduction number R of SARS-CoV 2 (the virus causing COVID-19) for
various countries over time.

## Usage

This project assumes that you are using a non-ancient Linux
distribution which has [Python3](https://python.org) and
[git](https://git-scm.com) installed. If you want to visualize the
results, having [gnuplot](http://www.gnuplot.info) also installed is
highly advised.

First, you need to clone (or update, if you already ran the script in
the past) the input data from [Johns Hopkins
University](https://github.com/CSSEGISandData/COVID-19):

```terminal
./updateData.sh
```

For most countries, you can then extract the curve of the estimated
basic reproduction number like this:

```terminal
COUNTRY="Germany"
./estimateR.py "$COUNTRY" > "r-estimate-$COUNTRY.csv"
```

The result is contained in the file "r-estimate-$COUNTRY.csv" which
can be inspected via a spreadsheet program or visualized using tools
like `gnuplot`. To simplify the latter, another small shell script is
provided:

```terminal
COUNTRY="Germany"
./estimateAndVisualizeR.sh "$COUNTRY"
```

## Usage in the Web

```terminal
./extractAllCountries.sh
```

## Development Hints

How to add a new JavaScript dependency:

1. Add it to `package.json`
2. `npm install`
3. Use in `.html`
4. Adapt `collectHtmlDependencies.sh`
