FROM python:3.8-slim as base
LABEL maintainer="@lpofredc"

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    USERDIR=/xfer


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

WORKDIR $USERDIR
COPY --from=builder /app/dist/*.whl /tmp
RUN pip install /tmp/*.whl
RUN addgroup --system -gid 1001 xfer && adduser --system --home $USERDIR --uid 1001 --group xfer && chown -R xfer:xfer $USERDIR
USER xfer

VOLUME [$USERDIR]

ENTRYPOINT [ "gn2pg_cli" ]
