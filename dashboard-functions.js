var data = [];

// per-county data from the CSV file plus the calculated results
var inputData = {}

// list of all country names in the data set
var countryNames = [];

// data fed to plotly.js for visualization
var plotlyCountryData = {};

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

function updatePlot()
{
    var plotlyData = [];

    for (var c in plotlyCountryData) {
        plotlyData.push(...plotlyCountryData[c]);
    }

    var layout = {
        yaxis: { rangemode: 'tozero' }
    };
    
    Plotly.newPlot(/*domElementId=*/'mainplot', plotlyData, layout, {modeBarButtonsToRemove: ["toggleSpikelines", "resetScale2d"]});
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
}

// recalculate the data of all curved and update the ploted curves as
// well as the control elements.
function recalculateCurvesAndPlot()
{
    // play it safe and update the info labels for of the controls
    updateControlInfos();

    recalculateCurves();

    updatePlot();
}

function estimateR(countryName)
{
    // TODO: actual stuff
    return inputData[countryName].newCases;
}

function diamondPrincessEstimate(countryName)
{
    // TODO: actual stuff
    return inputData[countryName].newCases;
}

function diamondPrincessEstimateRatio(countryName)
{
    // TODO: actual stuff
    return inputData[countryName].totalCases;
}

function smoothenData(d)
{
    // TODO: box filter
    return d;
}

function normalizeData(countryName, d)
{
    // TODO: divide all array elementsby the number of captia of the
    // country
    return d;
}

function recalculateCurves()
{
    curveType = document.getElementById("curveType").value;

    var normalize = false; //document.getElementById("checkboxNormalize").checked;

    var showRaw = document.getElementById("checkboxShowRaw").checked;
    var showSmoothened = document.getElementById("checkboxShowSmoothened").checked;
    
    // update data fed to the plotly widget
    plotlyCountryData = {}
    for (var countryName in inputData) {
        countryPlotlyData = []

        var dates = inputData[countryName].dates;
        var dr = null;
        var ds = null;
        var drCaption = countryName;
        var dsCaption = countryName;

        if (curveType == "R"){
            dr = estimateR(countryName);
            ds = smoothenData(dr);

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
            ds = smoothenData(dr);
            dates = inputData[countryName].dates.slice(0, dr.length)

            drCaption += ", \"Diamond Princess Estimate\" to Total Cases";
            dsCaption += ", Smoothened \"Diamond Princess Estimate\" Total Cases";

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
                name: drCaption,
            });
        }
        if (showSmoothened) {
            countryPlotlyData.push({
                x: inputData[countryName].dates,
                y: ds,

                mode: 'lines',
                name: dsCaption,
            });
        }

        plotlyCountryData[countryName] = countryPlotlyData;
    }
}

function addCountry(country)
{
    // check the country's check box
    elem = document.getElementById("checkbox"+country);

    if (!elem)
        return;

    elem.checked = true;

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

                               for (let i = 1; i < results.data.length; i++) {
                                   xPoints.push(results.data[i][0]);

                                   yPointsTotalCases.push(results.data[i][colIdxTotalCases]);
                                   yPointsNewCases.push(results.data[i][colIdxNewCases]);
                                   yPointsTotalDeaths.push(results.data[i][colIdxTotalDeaths]);
                                   yPointsNewDeaths.push(results.data[i][colIdxNewDeaths]);
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
}

function removeCountry(country)
{
    // check the country's check box
    elem = document.getElementById("checkbox"+country);
    elem.checked = false;

    delete inputData[country];
    delete plotlyCountryData[country];
}

function clickedOnCountry(country)
{
    elem = document.getElementById("checkbox"+country);

    if (elem.checked)
        addCountry(country);
    else 
        removeCountry(country);

    updatePlot();
}

function initPlot()
{
    updateControlInfos();

    readCountryList(function () {
        var countriesHtml = "";
        for (var countryIdx in countryNames) {
            var country = countryNames[countryIdx];
            if (country == "")
                continue;
            countriesHtml += "<li>\n";
            countriesHtml += "<input id=\"checkbox"+country+"\" type=\"checkbox\" value=\""+country+"\" onchange=\"clickedOnCountry('"+country+"')\" />\n";
            countriesHtml += "<label for=\"checkbox"+country+"\">"+country+"</label>\n";
            countriesHtml += "</li>\n";
        }

        document.getElementById("countrylist").innerHTML = countriesHtml;

        addCountry("Germany");
        addCountry("Italy");
        addCountry("US");

        updateControlInfos();
        updatePlot();
    });
}
