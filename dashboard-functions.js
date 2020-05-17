var data = [];
var countryList = [];
var countryDataToPlot = {};

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
                                       countryList.push(results.data[i][0])
                               }
                           }
                       });
            if (onComplete)
                onComplete();
        }
    };
    clRawFile.send(null);
};

function updatePlot()
{
    var plotlyData = [];

    for (var c in countryDataToPlot) {
        plotlyData.push(...countryDataToPlot[c]);
    }

    var layout = {
        yaxis: { rangemode: 'tozero' }
    };
    
    Plotly.newPlot(/*domElementId=*/'mainplot', plotlyData, layout, {modeBarButtonsToRemove: ["toggleSpikelines", "resetScale2d"]});
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
                           delimitersToGuess: [ ' ' ],
                           complete: function(results) {
                               let xPoints = [];
                               let yPointsR = [];
                               let yPointsSmoothR = [];

                               let colIdxR = 5;
                               let colIdxSmoothR = 11;

                               for (let i = 1; i < results.data.length; i++) {
                                   xPoints.push(results.data[i][0]);
                                   yPointsR.push(results.data[i][colIdxR]);
                                   yPointsSmoothR.push(results.data[i][colIdxSmoothR]);
                               }

                               var data = [];
                               data.push({
                                   x: xPoints,
                                   y: yPointsSmoothR,
                                   mode: 'lines',
                                   name: country + ", " + results.data[0][colIdxSmoothR],
                               });

                               countryDataToPlot[country] = data;
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

    delete countryDataToPlot[country];
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
    readCountryList(function () {
        var countriesHtml = "";
        for (var countryIdx in countryList) {
            var country = countryList[countryIdx];
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

        updatePlot();
    });
}
