FROM python:3.10-slim-buster as base
LABEL maintainer="@lpofredc"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y libpq-dev

FROM base as builder

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install poetry

COPY . .
RUN poetry install
RUN poetry build

FROM base as final

RUN groupadd -r -g 1000 xfer && useradd --no-log-init -r -g 1000 -d /home/xfer -m -u 1000 xfer && \
    chown -R xfer /home/xfer
#    echo "export PATH=$PATH:~/.local/bin" >> ~/.profile

COPY --from=builder /app/dist/*.whl /tmp/

RUN pip install /tmp/*.whl

USER xfer
RUN mkdir /home/xfer/.gn2pg
# VOLUME /home/xfer/.gn2pg

#COPY docker-entrypoint.sh /entrypoint.sh
#ENTRYPOINT ["/bin/sh", "entrypoint.sh"]

ENTRYPOINT ["gn2pg_cli"]
