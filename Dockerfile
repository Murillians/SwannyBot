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
    #manually install latest wavelink because of breaking changes, remove upon release of wavelink >2.5.1
    pip install -U git+https://github.com/PythonistaGuild/Wavelink.git --force-reinstall &&\
    chmod +x start.sh
ENV TZ=America/New_York
#CMD [ "/bin/bash","-c","java -jar /swannybot/wavelink/Lavalink.jar & python3 /swannybot/swanny_bot.py" ]
CMD ["/swannybot/start.sh"]

