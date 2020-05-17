FROM debian:latest

# Config and templates
VOLUME [ "/etc/service" ]

# Python logs
VOLUME [ "/var/log/service" ]

ADD noteandtag /home/noteandtag
ADD requirements.txt /home/requirements.txt

WORKDIR /home

ENV PYTHONPATH "${PYTHONPATH}:/home"

RUN apt-get upgrade -y && \
    apt-get update -y && \
    apt-get install -y python3 python3-pip && \
    python3 -m pip install -r requirements.txt

CMD [ "python3", "-m", "noteandtag", "/etc/service" ]

EXPOSE 8080
