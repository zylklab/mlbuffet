ARG PYTHON_VERSION=3.8

FROM python:${PYTHON_VERSION}

WORKDIR usr/src/flask_app

COPY requirements.txt .
COPY install_ml_library.sh .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY api_test.py .

COPY utils utils
RUN mkdir /home/logs

# Run integration testing
RUN ["chmod", "+x", "./api_test.py"]
#RUN python ./api_test.py

# HTTP
ENTRYPOINT bash ./install_ml_library.sh && gunicorn -w 1 -b 0.0.0.0:8000 app:server

