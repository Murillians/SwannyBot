#SwannyBot Dockerfile
#todo: optimize image, 1.5gb and several minutes on endeavor is not acceptable
#needs application.yml, swannybottokens.py, special_cog.py, and swannybot.db in /config to run successfuly
#run from python:latest because debian currently does not have python 3.11 stable
FROM python:3.11-slim-bookworm
RUN mkdir -p /swannybot
WORKDIR /swannybot
COPY . .
RUN apt-get update -y &&\
    apt-get install -y bash &&\
    apt-get install -y ffmpeg &&\
    apt-get install -y  openjdk-17-jdk &&\
    apt-get install -y nano &&\
    pip install -r requirements.txt --user &&\
    apt-get install -y curl &&\
    #until twitter fixes make it to pip
    pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz &&\
    curl -JL https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar -o ./wavelink/Lavalink.jar &&\
    chmod +x start.sh
ENV TZ=America/New_York
CMD ["/swannybot/start.sh"]

