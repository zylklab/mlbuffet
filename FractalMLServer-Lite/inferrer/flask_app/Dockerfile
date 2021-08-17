ARG PYTHON_VERSION=3.8

FROM python:${PYTHON_VERSION}

WORKDIR usr/src/flask_app

COPY app.py .
COPY wsgi.py .
COPY modelhost_talker.py .
COPY requirements.txt .
COPY api_test.py .
COPY cache/inferrer-cache.json /.cache/inferrer-cache.json

COPY utils utils
RUN mkdir /home/logs

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

#run integration testing
RUN ["chmod", "+x", "./api_test.py"]
RUN python ./api_test.py

#http
CMD ["gunicorn", "-w", "1", "-k", "gevent", "--worker-connections", "1000", "-b", "0.0.0.0:8000", "wsgi:server"]

