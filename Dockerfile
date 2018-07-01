FROM ubuntu:18.04 as pyppeteer_installed

###########################################################################
#
# pyppeteer + Chrome installation
#
###########################################################################

RUN apt-get update && apt-get install -y python3-pip

RUN pip3 install pyppeteer

RUN apt update && apt install -y libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libgcc1 libgdk-pixbuf2.0-0 \
    libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
    libpangocairo-1.0-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 \
    libxrender1 libxss1 libxtst6 bash xdg-utils && apt-get clean

RUN groupadd chrome && useradd -g chrome -s /bin/bash -G audio,video chrome \
    && mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome

RUN apt-get update && apt-get install -y fonts-noto-cjk locales && apt-get clean

USER chrome
RUN python3 -c '__import__("pyppeteer.chromium_downloader").chromium_downloader.download_chromium()'

USER root
RUN locale-gen en_US.UTF-8
USER chrome
ENV LC_ALL=en_US.UTF-8

ADD ./requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

ADD ./server.py /tmp/server.py

FROM pyppeteer_installed as test
ADD ./requirements-dev.txt /tmp
RUN pip3 install -r /tmp/requirements-dev.txt
RUN python3 -m flake8 /tmp/server.py
RUN python3 -m nose /tmp/server.py

FROM pyppeteer_installed
ENV QUART_APP=/tmp/server.py
EXPOSE 5000
CMD ["python3", "-m", "quart", "run", "-h", "0.0.0.0"]
