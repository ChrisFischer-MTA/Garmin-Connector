FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=america/los_angeles


# Base packages
RUN apt update && \
    apt install --no-install-recommends -q -y \
    software-properties-common \
    ca-certificates \
    wget \
    curl \
    ocl-icd-libopencl1 \
    python3-pip \
    python3-venv \
    git \
    python-is-python3

# First, let's make the directory where we're going to work out of
RUN mkdir /opt/garmin
RUN mkdir /opt/garmin/data
RUN mkdir /opt/garmin/code
RUN cd /opt/garmin/code
RUN git clone https://github.com/ChrisFischer-MTA/Garmin-Connector.git /opt/garmin/code
RUN printf "cd /opt/garmin/code \
\ngit pull \
\npython -m venv venv \
\nsource venv/bin/activate \
\npython -m pip install garmindb ipython snakemd ipyleaflet ipywidgets fastapi[standard] \
\npython -m fastapi dev --host 0.0.0.0 /opt/garmin/code/main.py" > /opt/garmin/start.sh

RUN cat /opt/garmin/start.sh
RUN mkdir /root/.GarminDb

ENTRYPOINT ["/bin/bash", "/opt/garmin/start.sh"]

