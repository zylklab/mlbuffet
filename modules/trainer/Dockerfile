ARG PYTHON_VERSION=3.8.1

FROM python:${PYTHON_VERSION}

# Tread lightly
RUN useradd -s /bin/bash trainer
RUN mkdir /home/trainer
RUN chown -R trainer:trainer /home/trainer


WORKDIR /home/trainer
RUN pip install --upgrade pip
RUN pip install requests kubernetes

COPY --chown=trainer:trainer entrypoint.sh entrypoint.sh
COPY --chown=trainer:trainer apoptosis.py apoptosis.py
RUN chmod +x entrypoint.sh
RUN chmod +x apoptosis.py

USER trainer

ENTRYPOINT /home/trainer/entrypoint.sh

