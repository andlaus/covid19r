#!/usr/bin/env bash
mkdir -p html
cp --parents node_modules/select2/dist/css/select2.css html/
cp --parents node_modules/jquery/dist/jquery.min.js html/
cp --parents node_modules/select2/dist/js/select2.min.js html/
cp --parents *.{js,html,css} html/
cp -pdfR processed-data html/
