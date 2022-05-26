#!/bin/bash

# Do your curly thing
curl inferrer:8000/api/v1/train/download_buildenv --output environment.zip;

# Unzip the environment
unzip environment.zip;

cd trainerfiles

#Run the script to get the model name and tag env variables
bash environment.sh

#Install requirements, run training and send model back to inferrer
pip install -r requirements.txt;
python3 train.py;
python3 find.py $MODEL_NAME $MODEL_TAG;

