# COVID-19 Effective Reproduction Factor Estimator

This Repository contains python and web scripts to estimate the
effective reproduction number R of SARS-CoV 2 (the virus causing
COVID-19) for various countries over time.

## Usage

The easiest way to use these scripts is by pointing your web browser
to the online version:

https://poware.org/covid19

That said, you are very welcome experiment with this data
yourself. The easiest version to do so is to use the python version of
the scripts. In this context, we assume that you are using a
non-ancient Linux distribution which has [Python3](https://python.org)
and [git](https://git-scm.com) installed. If you want to visualize the
results, having [gnuplot](http://www.gnuplot.info) installed is highly
advised, although you can inspect and process the results using any
modern spreadsheet program.

First, you need to clone or update the source data from [Johns Hopkins
University](https://github.com/CSSEGISandData/COVID-19):

```terminal
./updateData.sh
```

For most countries, you can then extract the curve of the estimated
effective reproduction number like this:

```terminal
COUNTRY="Germany"
./estimateR.py "$COUNTRY" > "r-estimate-$COUNTRY.csv"
```

The result is contained in the file "r-estimate-$COUNTRY.csv" which
can be inspected via a spreadsheet program or visualized using tools
like `gnuplot`. To simplify the latter, a small shell script is
provided:

```terminal
COUNTRY="Germany"
./estimateAndVisualizeR.sh "$COUNTRY"
```

## Deployment on the Web

If you want to deploy the interactive version on your own web server,
you need to have the npm package manager installed. Then, run

```terminal
./extractAllCountries.sh
npm install
./collectHtmlDependencies.sh
```

The results are contained in the 'html' subdirectory. To deploy it,
copy it somewhere to your webserver. Any webserver which is able to
serve static files will do.

## Development Hints

Adding a new JavaScript dependency can be achieved like this:

1. Adapt `package.json`
2. Run `npm install`
3. Use it in the `.html` and `.js` files
4. Adapt `collectHtmlDependencies.sh`
