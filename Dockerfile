#SwannyBot Dockerfile
#todo: optimize image, 1.5gb and several minutes on endeavor is not acceptable
#needs application.yml, swannybottokens.py, special_cog.py, and swannybot.db in /config to run successfuly
#run from python:latest because debian currently does not have python 3.11 stable
FROM python:latest
RUN mkdir -p /swannybot
WORKDIR /swannybot
COPY . .
RUN apt-get update -y &&\
    apt-get upgrade -y &&\
    pip install --upgrade pip &&\
    apt-get install -y bash &&\
    apt-get install -y ffmpeg &&\
    apt-get install -y nano &&\
    pip install -r requirements.txt --user &&\
    #temp update to ytdlp because of FUCKING ELON AGAIN
    pip install -U https://github.com/yt-dlp/yt-dlp.git --force-reinstall
ENV TZ=America/New_York
CMD ["/swannybot/start.sh"]