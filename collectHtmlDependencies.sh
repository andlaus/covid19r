#!/usr/bin/env bash
mkdir -p html
cp --parents node_modules/plotly.js/dist/plotly-basic.min.js html/
cp --parents node_modules/papaparse/papaparse.min.js html/
cp --parents node_modules/jquery/dist/jquery.min.js html/
cp --parents node_modules/select2/dist/css/select2.min.css html/
cp --parents node_modules/select2/dist/js/select2.min.js html/
cp --parents node_modules/bootstrap/dist/js/bootstrap.min.js html/
cp --parents node_modules/bootstrap/dist/css/bootstrap.css html/
cp --parents node_modules/bootstrap/dist/css/bootstrap.css.map html/
cp --parents node_modules/bootstrap/dist/js/bootstrap.js html/
cp --parents node_modules/@fortawesome/fontawesome-free/css/all.css html/
cp --parents -R node_modules/@fortawesome/fontawesome-free/webfonts/ html/
cp --parents *.{js,svg,html,css} html/
cp -pdfR processed-data html/
