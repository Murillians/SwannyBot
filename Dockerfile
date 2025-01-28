#SwannyBot Dockerfile
#todo: optimize image, 1.5gb and several minutes on endeavor is not acceptable
#needs application.yml, swannybottokens.py, special_cog.py, and swannybot.db in /config to run successfuly
FROM python:latest
RUN mkdir -p /swannybot
WORKDIR /swannybot
COPY . .
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update -y &&\
    apt-get upgrade -y &&\
    pip install --upgrade pip &&\
    apt-get install -y bash &&\
    apt-get install -y ffmpeg &&\
    apt-get install -y nano &&\
    pip install -r requirements.txt --user &&\
    pip install -U git+https://github.com/PythonistaGuild/Wavelink.git --force-reinstall
ENV TZ=America/New_York
CMD ["/swannybot/start.sh"]