#!/bin/bash

cd ./lambda
mkdir .tmp
cp * .tmp
cd .tmp
pip install -r requirements.txt -t .
zip -r ../../lambda.zip ./*
cd ..
rm -r .tmp
