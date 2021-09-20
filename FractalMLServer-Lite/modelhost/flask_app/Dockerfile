ARG PYTHON_VERSION=3.6.7

FROM python:${PYTHON_VERSION}

WORKDIR usr/src/flask_app

COPY app.py .
COPY wsgi.py .

COPY requirements.txt .
COPY api_test.py .

COPY utils utils
COPY models models
RUN mkdir /home/logs

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# Run integration testing
RUN ["chmod", "+x", "./api_test.py"]
RUN python ./api_test.py

# HTTP
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "wsgi:server"]

