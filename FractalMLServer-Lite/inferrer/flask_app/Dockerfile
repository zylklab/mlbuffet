ARG PYTHON_VERSION=3.6.7

FROM python:${PYTHON_VERSION}

WORKDIR usr/src/flask_app

COPY app.py .
COPY wsgi.py .
COPY requirements.txt .
COPY api_test.py .
#COPY init.sh .

RUN pwd
COPY utils utils
COPY modelhost_utils modelhost_utils

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

#run integration testing
RUN mkdir /home/logs

COPY cache/inferrer-cache.json /.cache/inferrer-cache.json

#Run the API test script to check if methods work
RUN ["chmod", "+x", "./api_test.py"]
RUN python ./api_test.py

#http
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "wsgi:server"]



