ARG PYTHON_VERSION=3.8

FROM python:${PYTHON_VERSION}

WORKDIR usr/src/flask_app

COPY requirements.txt .

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 iputils-ping nmap -y
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY wsgi.py .
COPY modelhost_talker.py .
COPY api_test.py .
COPY cache/inferrer-cache.json /.cache/inferrer-cache.json

COPY utils utils
RUN mkdir /home/logs

#run integration testing
RUN ["chmod", "+x", "./api_test.py"]
RUN python ./api_test.py

#http
CMD ["gunicorn", "-w", "1", "-k", "gevent", "--worker-connections", "1000", "-b", "0.0.0.0:8000", "wsgi:server"]

