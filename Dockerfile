#SwannyBot Dockerfile
#todo: optimize image, 1.5gb and several minutes on endeavor is not acceptable
#needs application.yml, swannybottokens.py, special_cog.py, and swannybot.db in /config to run successfuly
FROM python:latest
RUN mkdir -p /swannybot
WORKDIR /swannybot
COPY . .
# The installer requires curl (and certificates) to download the release archive
RUN apt-get update &&\
    apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"
RUN apt-get install -y bash &&\
    apt-get install -y ffmpeg &&\
    apt-get install -y nano
ENV TZ=America/New_York
CMD ["uv" "run" "swanny_bot.py"]