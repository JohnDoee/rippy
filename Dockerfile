FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN apt update && \
    apt install -y supervisor ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir /code
WORKDIR /code

COPY . /code/
RUN python setup.py install

COPY supervisor.conf /
COPY manage.py /
COPY start-supervisor.sh /
RUN chmod +x /start-supervisor.sh

WORKDIR /

ENV RIPPY_CONCURRENCY=2

CMD ["bash", "/start-supervisor.sh"]