FROM python:3.8-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update && apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
    build-essential libpq-dev netcat
RUN mkdir -p $VIRTUAL_ENV
RUN python3.8 -m venv $VIRTUAL_ENV

# copy entrypoint.sh
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
COPY . /usr/src/app/

WORKDIR /usr/src/app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]