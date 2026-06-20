FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=america/los_angeles


# Base packages
#RUN apt update && \
#    apt install --no-install-recommends -q -y \
#    software-properties-common \
#    ca-certificates \
#    wget \
#    curl \
#    ocl-icd-libopencl1 \
#    python3-pip \
#    python3-venv \
#    git \
#    python-is-python3

# First, let's make the directory where we're going to work out of
RUN mkdir /opt/garmin
RUN mkdir /opt/garmin/data
RUN mkdir /opt/garmin/code
RUN cd /opt/garmin/code
COPY ./main.py /opt/garmin/code
COPY ./GarminConnectConfig.json /opt/garmin/code
RUN pip install garmindb ipython snakemd ipyleaflet ipywidgets fastapi[standard] folium 

ENV GARMIN_USERNAME=joe@shmoe.com
ENV GARMIN_PASSWORD=yourpassword

RUN printf "cd /opt/garmin/code \
\npython3 -c \"import json, os; c=json.load(open('/opt/garmin/code/GarminConnectConfig.json')); c['credentials']['user']=os.environ.get('GARMIN_USERNAME', c['credentials']['user']); c['credentials']['password']=os.environ.get('GARMIN_PASSWORD', c['credentials']['password']); json.dump(c, open('/root/.GarminDb/GarminConnectConfig.json', 'w'), indent=4)\" \
\ngarmindb_cli.py -d -l -a \
\ngarmindb_cli.py --rebuild_db \
\npython -m fastapi dev --host 0.0.0.0 /opt/garmin/code/main.py " > /opt/garmin/start.sh

RUN mkdir /root/.GarminDb

ENTRYPOINT ["/bin/bash", "/opt/garmin/start.sh"]

