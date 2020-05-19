#! /bin/bash

pushd . > /dev/null
if test -d "COVID-19"; then
    cd COVID-19
    git pull
else
    git clone --depth=1 https://github.com/CSSEGISandData/COVID-19
fi

popd > /dev/null
