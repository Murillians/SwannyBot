#SwannyBot Dockerfile
#todo: optimize image, 1.5gb and several minutes on endeavor is not acceptable
#needs application.yml, swannybottokens.py, special_cog.py, and swannybot.db in /config to run successfuly
FROM python:latest
RUN mkdir -p /swannybot
WORKDIR /swannybot
RUN apt-get update -y &&\
    apt-get upgrade -y &&\
    pip install --upgrade pip &&\
    apt-get install -y bash &&\
    apt-get install -y ffmpeg &&\
    apt-get install -y nano
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN . /opt/venv/bin/activate &&\
    pip install -r requirements.txt &&\
    pip install -U git+https://github.com/PythonistaGuild/Wavelink.git --force-reinstall \
COPY . .
ENV TZ=America/New_York
CMD . /opt/venv/bin/activate && exec python swanny_bot.py