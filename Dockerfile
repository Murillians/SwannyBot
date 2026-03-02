#SwannyBot Dockerfile
#todo: optimize image, 1.5gb and several minutes on endeavor is not acceptable
#needs application.yml, swannybottokens.py, special_cog.py, and swannybot.db in /config to run successfuly
FROM python:latest
RUN mkdir -p /swannybot
WORKDIR /swannybot
COPY . .
#install fork of wavelink for DAVE compatibility
RUN apt-get update -y &&\
    apt-get upgrade -y &&\
    curl -fsSL https://deno.land/install.sh | sh &&\
    pip install --upgrade pip &&\
    apt-get install -y bash &&\
    apt-get install -y ffmpeg &&\
    apt-get install -y nano &&\
    pip install -r requirements.txt --user &&\
    pip install -U git+https://github.com/atefcodes/Wavelink.git --force-reinstall &&\
    chmod +x start.sh
ENV TZ=America/New_York
CMD ["/swannybot/start.sh"]