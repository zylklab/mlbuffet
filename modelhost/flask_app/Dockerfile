ARG PYTHON_VERSION=3.6.7

FROM python:${PYTHON_VERSION}

WORKDIR usr/src/flask_app

RUN apt-get update -y
RUN apt-get install -y libprotobuf-dev protobuf-compiler

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY api_test.py .

COPY utils utils
COPY models models
RUN mkdir /home/logs

# Run integration testing
RUN ["chmod", "+x", "./api_test.py"]
RUN python ./api_test.py

# HTTP
CMD ["gunicorn", "--timeout", "1000","-w", "1", "-b", "0.0.0.0:8000", "app:server"]

