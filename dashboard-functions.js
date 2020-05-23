var data = [];

// per-county data from the CSV file plus the calculated results
var inputData = {}

// list of all country names in the data set
var countryNames = [];

// data fed to plotly.js for visualization
var plotlyCountryData = {};

// ranges for the last autorange operations. Used to decide when to do
// auto range and when not.
var autoRangeX = null;
var autoRangeY = null;

// the index of the color which the next newly selected country gets
// assigned to.
var nextCountryColorIdx = 0;
// the color indices of countries which have already been added
var countryColorIndices = {};

function readCountryList(onComplete = null)
{
    var clRawFile = new XMLHttpRequest();
    clRawFile.open("GET", "processed-data/countries.csv", false);
    clRawFile.overrideMimeType("text/csv");
    clRawFile.onreadystatechange = function ()
    {
        if(clRawFile.readyState === 4 && (clRawFile.status === 200 || clRawFile.status == 0))
        {
            Papa.parse(clRawFile.responseText,
                       {
                           delimitersToGuess: [ ' ' ],
                           complete: function(results) {
                               for (var i = 0; i < results.data.length; i++) {
                                   if (results.data[i].length > 0)
                                       countryNames.push(results.data[i][0])
                               }
                           }
                       });
            if (onComplete)
                onComplete();
        }
    };
    clRawFile.send(null);
}

function arrayEqual(a, b)
{
    if (a.length != b.length)
        return false;

    for (var i = 0; i < a.length; i++) {
        if (a[i] != b[i])
            return false;
    }

    return true;
}

function updatePlot(autoscale = false)
{
    var domElem = document.getElementById("mainplot");

    var layout = {
        showlegend: true,
        legend: {
            bgcolor: "#ffffff88",
            x: 1,
            xanchor: 'right',
            y: 1
        },

        xaxis: {
            rangemode: 'tozero',
        },

        yaxis: {
            rangemode: 'tozero',
        },

        margin: {
            l: 40,
            r: 40,
            t: 40,
            b: 40,
            pad: 0,
        },
    };

    if (!domElem.layout)
        // for the first plotting operation, we always use autoscale
        autoscale = true;

    if (!autoscale &&
        arrayEqual(autoRangeX, domElem.layout.xaxis.range) &&
        arrayEqual(autoRangeY, domElem.layout.yaxis.range)) {
        // we are not in forced autoscale mode but the axis have not
        // been changed manually, so we autoscale them
        autoscale = true;
    }

    if (!autoscale) {
        layout.xaxis.range = domElem.layout.xaxis.range.slice();
        layout.yaxis.range = domElem.layout.yaxis.range.slice();
    }
        
    var plotlyData = [];

    for (var c in plotlyCountryData) {
        plotlyData.push(...plotlyCountryData[c]);
    }
    
    Plotly.newPlot(/*domElementId=*/'mainplot', plotlyData, layout, {modeBarButtonsToRemove: ["toggleSpikelines", "resetScale2d"]});

    if (autoscale) {
        // remember the current range. we want to copy the arrays, not
        // just store a reference, so we have to call slice()
        autoRangeX = domElem.layout.xaxis.range.slice();
        autoRangeY = domElem.layout.yaxis.range.slice();
    }
}

function updateInfectivityPlot()
{
    // resize the DOM element to its proper height
    var weightsPlotElem = document.getElementById("infectivityplot");
    var widthPx = weightsPlotElem.getBoundingClientRect().width

    weightsPlotElem.style.height = (widthPx/2) + "px";

    var numDaysInfectious = parseFloat(document.getElementById("infectivityDays").value);

    var xAxis = [];
    var yAxis = [];
    for (var i = 0; i < numDaysInfectious; i++) {
        xAxis.push(i + infectivityOffset);
        yAxis.push(infectivityWeights[i]);
    }

    var plotlyData = [];
    plotlyData.push({
        x: xAxis,
        y: yAxis,

        type: "bar",
    });
    
    var layout = {
        xaxis: {
            title: "Days after Report",
            rangemode: 'tozero',
            fixedrange: true,
        },
        yaxis: {
            title: "Infectivity",
            rangemode: 'tozero',
            showticklabels: false,
            fixedrange: true,
        },

        margin: {
            l: 10,
            r: 10,
            t: 20,
            b: 40,
            pad: 0,
        },
    };
    
    Plotly.newPlot(/*domElementId=*/'infectivityplot', plotlyData, layout, {displayModeBar: false});
}

// update the parameter slider info elements and the visualization of the binomial distribution
function updateControlInfos()
{
    var sliders = document.getElementsByClassName("range");
    for (var i = 0; i < sliders.length; i++) {
        var slider = sliders[i];

        var sliderInfo = document.getElementById(slider.id + "Info");

        if (!sliderInfo) {
            // oops; bug in the HTML
            console.log("WARNING: Slider "+slider.id+" does not have any info element!");
            continue;
        }

        sliderInfo.innerHTML = slider.value;
    }

    updateInfectivityWeights();
    updateInfectivityPlot();
}

// recalculate the data of all curved and update the ploted curves as
// well as the control elements.
function recalculateCurvesAndPlot(autoscale = false)
{
    // play it safe and update the info labels for of the controls
    updateControlInfos();

    recalculateCurves();

    updatePlot(autoscale);
}

function nChosek(n, k)
{
    var k = Math.min(k, n-k)

    var numer = 1.0;
    for (var i = n; i > n-k; i--)
        numer *= i;

    var denom = 1.0;
    for (var i = 1; i < k+1; i++)
        denom *= i;

    return numer / denom;
}

var infectivityOffset = -3;
var infectivityWeights = [];

function updateInfectivityWeights()
{
    infectivityWeights = [];

    var numDaysInfectious = parseFloat(document.getElementById("infectivityDays").value);
    infectivityOffset = parseFloat(document.getElementById("firstDayActive").value);
    var k = parseFloat(document.getElementById("peakDayActive").value);

    var s = 0.0;
    for (var i = 1; i < numDaysInfectious + 1; i ++) {
        var p = i / (numDaysInfectious + 1);

        var y = nChosek(numDaysInfectious + 1, k)
                * Math.pow(p, k)
                * Math.pow(1 - p, numDaysInfectious + 1 - k);

        s += y;
        infectivityWeights.push(y);
    }

    // normalize the weight array. this might not be necessary, but
    // I'm a statistics n00b and better safe than sorry...
    for (var i = 1; i < infectivityWeights.length; i ++)
        infectivityWeights[i] /= s;
}

function estimateR(countryName)
{
    countryData = inputData[countryName];

    // creating an array of a given length full of zeros in JavaScript
    // is -- um -- interesting...
    var result = [];
    for (var i = 0; i < countryData.dates.length; i++)
        result.push(0.0);

    for (var i = 0; i < result.length; i++) {
        // distribute the cases of day i according to the infectivity data
        for (var j = 0; j < infectivityWeights.length; j++) {
            var dayIdx = i + infectivityOffset + j;

            if (dayIdx < 0)
                continue;
            else if (dayIdx >= result.length)
                continue;

            result[dayIdx] += countryData.newCases[i] * infectivityWeights[j];
        }
    }

    // compute the estimated R factor by dividing the actually seen
    // cases of a day by the attributable weight (currently in the
    // result array)
    for (var i = 0; i < result.length; i++) {
        w = result[i];

        if (w < 10.0) {
            // do not calculate R factors for dates where we have too
            // few infectious cases: It does not make sense.
            result[i] = null;
        }
        else if (!w) {
            // we do not have enough past cases to calculate an R
            // factor for this day.
            if (countryData.newCases[i] > 0)
                result[i] = 3.0;
            else
                result[i] = 0.0;
        }
        else
            result[i] = countryData.newCases[i] / w;
    }

    return result;
}

function diamondPrincessEstimate(countryName)
{
    countryData = inputData[countryName];

    var result = [];

    // We define the "Diamond Pricess Estimate" for a given day as the
    // number of reported deaths in 14 days divided by the lethality
    // on the Diamond Princess cruise ship. (i.e., 13/712 = 1.83%) The
    // assumption is that new cases are reported 7 days after
    // infection and if they end deadly, death will occur 21 days
    // after infection.
    for (var i = 13; i < inputData[countryName].newDeaths.length; i++) {
        if (countryData.newDeaths[i])
            result.push(countryData.newDeaths[i] / (13./712));
        else
            result.push(null);
    }

    for (var i = Math.max(0, inputData[countryName].newDeaths.length - 14);
         i < inputData[countryName].newDeaths.length;
         i++) {
        result.push(null);
    }

    return result;
}

function diamondPrincessEstimateRatio(countryName)
{
    var countryData = inputData[countryName];
    var dpe = diamondPrincessEstimate(countryName);
    var result = [];
    
    for (var i = 0; i < countryData.totalCases.length; i++) {
        if (dpe[i]) {
            if (countryData.newCases[i])
                result.push(dpe[i]/countryData.newCases[i]);
            else
                result.push(null);
        }
        else
            result.push(null);
    }
    
    return result;
}

function smoothenData(d, central = true)
{
    var n = parseFloat(document.getElementById("smoothenDays").value);

    // number of days before the day we want to calculate the average
    var offset = n - 1;
    if (central)
        offset = Math.floor(n/2);
    
    var result = [];

    // find the range where the raw data does not consist of just
    // null objects.
    var rawDataRange = [0, d.length];
    for (var i = 0; i + 1 < d.length && d[i] == null; i ++)
        rawDataRange[0] = i + 1;
    for (var i = d.length; i > rawDataRange[0]; --i) {
        rawDataRange[1] = i;
        if (d[i - 1] != null)
            break;
    }

    // box filter
    for (var i = 0; i < d.length; i ++) {
        var numValues = 0;
        var s = 0.0;

        for (var j = 0; j < n; j ++) {
            var k = i + j - offset;
            if (k < rawDataRange[0])
                continue;
            if (k >= rawDataRange[1])
                continue;

            if (d[k] == null)
                continue;

            s += d[k];
            numValues += 1;
        }

        if (i < rawDataRange[0] || i >= rawDataRange[1])
            result.push(null);
        else if (numValues > 0)
            result.push(s/numValues);
        else
            result.push(null);
    }
    
    return result;
}

function normalizeData(countryName, d)
{
    // TODO: divide all array elementsby the number of captia of the
    // country
    return d;
}

function getGlobalCountryIndex(countryName)
{
    for (var i = 0; i < countryNames.length; i++)  {
        if (countryNames[i] == countryName)
            return i;
    }
    
    return countryNames.length;
}

function recalculateCurves()
{
    updateInfectivityWeights();

    var colorListSmoothened = [
        '#1f77b4',  // muted blue
        '#ff7f0e',  // safety orange
        '#2ca02c',  // cooked asparagus green
        '#d62728',  // brick red
        '#9467bd',  // muted purple
        '#8c564b',  // chestnut brown
        '#e377c2',  // raspberry yogurt pink
        '#7f7f7f',  // middle gray
        '#bcbd22',  // curry yellow-green
        '#17becf'   // blue-teal
    ];

    var colorListRaw = [
        '#1f77b444',  // muted blue
        '#ff7f0e44',  // safety orange
        '#2ca02c44',  // cooked asparagus green
        '#d6272844',  // brick red
        '#9467bd44',  // muted purple
        '#8c564b44',  // chestnut brown
        '#e377c244',  // raspberry yogurt pink
        '#7f7f7f44',  // middle gray
        '#bcbd2244',  // curry yellow-green
        '#17becf44'   // blue-teal
    ];

    curveType = document.getElementById("curveType").value;

    var normalize = false; //document.getElementById("checkboxNormalize").checked;

    var showRaw = document.getElementById("checkboxShowRaw").checked;
    var showSmoothened = document.getElementById("checkboxShowSmoothened").checked;
    
    // update data fed to the plotly widget
    plotlyCountryData = {}
    for (var countryName in inputData) {
        countryPlotlyData = []

        var countryIdx = getGlobalCountryIndex(countryName);
        var countryColorIdx = countryColorIndices[countryName]%colorListRaw.length;

        var dates = inputData[countryName].dates;
        var dr = null;
        var ds = null;
        var drCaption = countryName;
        var dsCaption = countryName;

        if (curveType == "R"){
            dr = estimateR(countryName);

            // for the R factor estimate, it is more important to use
            // the specified number of data points for the newest than
            // to have a smaller delay for interior ones. we thus use
            // backward smoothing.
            ds = smoothenData(dr, /*central=*/false);

            drCaption += ", Estimated R";
            dsCaption += ", Smoothened Estimated R";

            // normalization does not make any sense for R factors!
        }
        else if (curveType == "C"){
            dr = inputData[countryName].totalCases;
            ds = smoothenData(dr);

            drCaption += ", Total Cases";
            dsCaption += ", Smoothened Total Cases";

            if (normalize) {
                dr = normalizeData(countryName, dr);
                ds = normalizeData(countryName, ds);

                drCaption += " per Captia";
                dsCaption += " per Captia";
            }
        }
        else if (curveType == "c"){
            dr = inputData[countryName].newCases;
            ds = smoothenData(dr);

            drCaption += ", New Cases";
            dsCaption += ", Smoothened New Cases";

            if (normalize) {
                dr = normalizeData(countryName, dr);
                ds = normalizeData(countryName, ds);

                drCaption += " per Captia";
                dsCaption += " per Captia";
            }
        }
        else if (curveType == "D"){
            dr = inputData[countryName].totalDeaths;
            ds = smoothenData(dr);

            drCaption += ", Total Deaths";
            dsCaption += ", Smoothened Total Deaths";

            if (normalize) {
                dr = normalizeData(countryName, dr);
                ds = normalizeData(countryName, ds);

                drCaption += " per Captia";
                dsCaption += " per Captia";
            }
        }
        else if (curveType == "d"){
            dr = inputData[countryName].newDeaths;
            ds = smoothenData(dr);

            drCaption += ", New Deaths";
            dsCaption += ", Smoothened New Deaths";

            if (normalize) {
                dr = normalizeData(countryName, dr);
                ds = normalizeData(countryName, ds);

                drCaption += " per Captia";
                dsCaption += " per Captia";
            }
        }
        else if (curveType == "P") {
            dr = diamondPrincessEstimate(countryName);
            ds = smoothenData(dr);
            dates = inputData[countryName].dates.slice(0, dr.length)

            drCaption += ", \"Diamond Princess Estimate\"";
            dsCaption += ", Smoothened \"Diamond Princess Estimate\"";

            if (normalize) {
                dr = normalizeData(countryName, dr);
                ds = normalizeData(countryName, ds);

                drCaption += " per Captia";
                dsCaption += " per Captia";
            }
        }
        else if (curveType == "p"){
            dr = diamondPrincessEstimateRatio(countryName);
            // for the DPE ratio, it is more important to use the
            // specified number of data points for the newest than to
            // have a smaller delay for interior ones. we thus use
            // backward smoothing.
            ds = smoothenData(dr, /*central=*/false);
            dates = inputData[countryName].dates.slice(0, dr.length)

            drCaption += ", \"Diamond Princess Estimate\" Ratio";
            dsCaption += ", Smoothened \"Diamond Princess Estimate\" Ratio";

            if (normalize) {
                dr = normalizeData(countryName, dr);
                ds = normalizeData(countryName, ds);

                drCaption += " per Captia";
                dsCaption += " per Captia";
            }
        }

        if (showRaw) {
            countryPlotlyData.push({
                x: inputData[countryName].dates,
                y: dr,

                mode: 'lines',
                line: {
                    color: colorListRaw[countryColorIdx],
                },
                name: drCaption,
            });
        }
        if (showSmoothened) {
            countryPlotlyData.push({
                x: inputData[countryName].dates,
                y: ds,

                mode: 'lines',
                line: {
                    color: colorListSmoothened[countryColorIdx],
                },
                name: dsCaption,
            });
        }

        plotlyCountryData[countryName] = countryPlotlyData;
    }
}

function addCountry(country)
{
    if (!(country in countryColorIndices)) {
        countryColorIndices[country] = nextCountryColorIdx;
        nextCountryColorIdx += 1;
    }

    // read in the data for that country
    var rawFile = new XMLHttpRequest();
    rawFile.open("GET", "processed-data/"+country+".csv", false);
    rawFile.overrideMimeType("text/csv");
    rawFile.onreadystatechange = function ()
    {
        if(rawFile.readyState === 4 && (rawFile.status === 200 || rawFile.status == 0))
        {
            Papa.parse(rawFile.responseText,
                       {
                           delimitersToGuess: [' '],
                           complete: function(results) {
                               let xPoints = [];
                               let yPointsTotalCases = [];
                               let yPointsNewCases = [];
                               let yPointsTotalDeaths = [];
                               let yPointsNewDeaths = [];

                               let colIdxTotalCases = 1;
                               let colIdxNewCases = 2;
                               let colIdxTotalDeaths = 3;
                               let colIdxNewDeaths = 4;

                               for (let i = 1; i < results.data.length - 1; i++) {
                                   xPoints.push(results.data[i][0]);

                                   yPointsTotalCases.push(parseFloat(results.data[i][colIdxTotalCases]));
                                   yPointsNewCases.push(parseFloat(results.data[i][colIdxNewCases]));
                                   yPointsTotalDeaths.push(parseFloat(results.data[i][colIdxTotalDeaths]));
                                   yPointsNewDeaths.push(parseFloat(results.data[i][colIdxNewDeaths]));
                               }

                               var cd = {
                                   dates: xPoints,

                                   totalCases: yPointsTotalCases,
                                   newCases: yPointsNewCases,
                                   totalDeaths: yPointsTotalDeaths,
                                   newDeaths: yPointsNewDeaths,
                               };

                               inputData[country] = cd;

                               recalculateCurves();
                           }
                       });
        }
    }
    rawFile.send(null);
    updatePlot();
}

function removeCountry(country)
{
    delete inputData[country];
    delete plotlyCountryData[country];
    updatePlot();
}

function initPlot()
{
    updateControlInfos();

    readCountryList(function () {
        $(document).ready(function() {
            var countries = [];
            for (var countryIdx in countryNames) {
                var country = countryNames[countryIdx];
                if (country == "")
                    continue;
                countries.push({
                    'id': country,
                    'text': country,
                });
            };
            $('#countrylist').select2({
                data: countries,
            });
            $('#countrylist').on('select2:select', function (e) {
                // console.log("select", e.params.data.id);
                addCountry(e.params.data.id);
            });
            $('#countrylist').on('select2:unselect', function (e) {
                console.log("unselect", e.params.data.id);
                removeCountry(e.params.data.id);
            });

            $("#countrylist option[value='Germany']").prop('selected', true);
            addCountry('Germany');

            $("#countrylist option[value='United States of America']").prop('selected', true);
            addCountry('United States of America');

            $('#countrylist').trigger('change.select2');

            updateControlInfos();
            updatePlot();
        });

    });
}
