================================
Rippy
================================
.. image:: ./logo.png

**Rip-it with Rippy**

Introduction
--------------------------------

Rippy is a downloader designed to scrape websites using a real web browser to find, e.g. video or downloadable files.
The targets are website that try to be scrape-resistant and where other downloaders had to give up.

The magic is that Rippy uses a real browser it controls so a lot of the normal anti-bot designs are inefficient,
e.g. scrambling javascript. To block Rippy you will have to block browsers.
I also enjoy a blocking arms-race, keeps my day bright and fulfilled.

Installation
--------------------------------

Currently the only distribution method officially provided is the docker-compose way but all it really requires is Chrome and Python.

.. code-block:: bash

    wget https://github.com/JohnDoee/rippy-docker/raw/master/docker-compose.yml

You should edit docker-compose.yml and change the media path. The path is where all the data is downloaded to.

.. code-block:: bash

    docker-compose up -d

Usage
--------------------------------

Head over to http://ip:51359 and add a job. It should start downloading or prompt you to do something manually.

If the status text says “Waiting” it means you need to open the browser and fill in a captcha or something alike. If you are using the docker-compose setup there should be a button in the upper-right corner of the website to open the browser. It will open a new window with a VNC to the hosted Chromium browser.

New scrapers
--------------------------------

Feel free to request a new scraper but there are a few requirements if you want me to implement them:
They are scrape resistant, as in, nobody else should be able to download. Check out tools like youtube-dl and JDownloader first.
They should not be using an encryption or behind paywall, i.e. I can’t do stuff like netflix (something like that is also not the target at all)

Currently a generic video-site scraper is on the slab as this project is a merge between a reddit post and a generic video-site scraper

Accompanied repositories
`````````````````````````````````

`Docker-compose file and docker chromium repository <https://github.com/JohnDoee/rippy-docker>`_

`Rippy webinterface <https://github.com/JohnDoee/rippy-webinterface>`_


TODO
--------------------------------

* [ ] Add (semi-)generic view player extractor
* [ ] Return (potentially proxied) URL to video instead of downloading

Docker images
--------------------------------

`Main backend component (this repository) <https://hub.docker.com/r/johndoee/rippy>`_

`Webapp and reverse proxy <https://hub.docker.com/r/johndoee/rippy-webapp>`_

`Chrome accessible via VNC <https://hub.docker.com/r/johndoee/rippy-vnc>`_

Logo / icon
--------------------------------

frog by habione 404 from the Noun Project

License
--------------------------------

MIT
