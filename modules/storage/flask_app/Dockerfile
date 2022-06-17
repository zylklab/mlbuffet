ARG PYTHON_VERSION=3.8

FROM python:${PYTHON_VERSION}

WORKDIR usr/src/flask_app

RUN apt-get update 
RUN apt-get install iputils-ping nmap -y
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir files
RUN mkdir logs

COPY app.py .
COPY utils utils

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "app:server"]
