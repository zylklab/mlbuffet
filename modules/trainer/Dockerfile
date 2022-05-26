ARG PYTHON_VERSION=3.8.1

FROM python:${PYTHON_VERSION}

# Tread lightly
RUN useradd -s /bin/bash trainer
RUN mkdir /home/trainer
RUN chown -R trainer:trainer /home/trainer


WORKDIR /home/trainer
RUN pip install --upgrade pip
RUN pip install requests

COPY --chown=trainer:trainer entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh

USER trainer

ENTRYPOINT /home/trainer/entrypoint.sh

