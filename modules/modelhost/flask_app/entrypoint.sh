#!/bin/bash

# get and install the required library to serve the model
ml_library=$(curl -X GET storage:8000/storage/models/"$TAG"/library | jq .ml_library |  tr -d 'n \n " \r \')
pip install "$ml_library"

# get the model and response headers
curl -D headers storage:8000/storage/models/"$TAG" --output model

# extract the filename from the headers and rename the model to it
filename=$(grep filename headers | cut -d "=" -f2 | tr -d '\r\n')
rm headers
mv model "$filename"

# start flask server
export ml_library
export filename
gunicorn -w 1 -b 0.0.0.0:8000 app:server --timeout 600
