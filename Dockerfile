#SwannyBot Dockerfile
#todo: optimize image, 1.5gb and several minutes on endeavor is not acceptable
#needs application.yml, swannybottokens.py, special_cog.py, and swannybot.db in /config to run successfuly
#run from python:latest because debian currently does not have python 3.11 stable
FROM python:3.12
RUN mkdir -p /swannybot
WORKDIR /swannybot
COPY . .
RUN apt-get update -y &&\
    apt-get upgrade -y &&\
    pip install --upgrade pip &&\
    apt-get install -y bash &&\
    apt-get install -y ffmpeg &&\
    apt-get install -y nano &&\
    pip install -r requirements.txt --user
ENV TZ=America/New_York
CMD ["/swannybot/start.sh"]