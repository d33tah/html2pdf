FROM ubuntu:18.04 as environment_prepared

###########################################################################
#
# <Chrome>
#
###########################################################################

# Can't remember where I pulled those deps from. Chrome .deb package's maybe?
RUN apt-get update && apt-get install -y --no-install-recommends libasound2 \
    libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 \
    libexpat1 libgcc1 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 \
    libnss3 libpango-1.0-0 libpangocairo-1.0-0 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
    libxrandr2 libxrender1 libxss1 libxtst6 bash xdg-utils && apt-get clean

RUN groupadd chrome && useradd -g chrome -s /bin/bash -G audio,video chrome \
    && mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome

###########################################################################
#
# </Chrome>
# <Pyppeteer>
#
###########################################################################

RUN apt-get update && apt-get install -y locales && apt-get clean

# Comment out if you need to shave 90MB off and don't need CJK (Asian) fonts:
RUN apt-get update && apt-get install --no-install-recommends -y \
    fonts-noto-cjk && apt-get clean

RUN apt-get update && apt-get install --no-install-recommends -y \
    python3-pip python3-setuptools && apt-get clean

RUN locale-gen en_US.UTF-8

USER chrome

RUN pip3 install pyppeteer
RUN python3 -c '__import__("pyppeteer.chromium_downloader").chromium_downloader.download_chromium()'

###########################################################################
#
# </Pyppeteer>
# <html2pdf>
#
###########################################################################

USER root
RUN apt-get update && apt-get install --no-install-recommends -y \
    dumb-init && apt-get clean
USER chrome

ADD ./requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

ADD ./server.py /tmp/server.py

###########################################################################
#
# </html2pdf>
# <test>
#
###########################################################################

FROM environment_prepared as test
ADD ./requirements-dev.txt /tmp
RUN pip3 install -r /tmp/requirements-dev.txt
RUN python3 -m flake8 /tmp/server.py
RUN python3 -m nose /tmp/server.py

###########################################################################
#
# </test>
# <final>
#
###########################################################################

FROM environment_prepared
USER chrome
ENV QUART_APP=/tmp/server.py
EXPOSE 5000
ENTRYPOINT ["/usr/bin/dumb-init", "--verbose", "--rewrite", "2:3", "--"]
CMD ["python3", "-m", "quart", "run", "-h", "0.0.0.0"]
