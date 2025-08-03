ARG PYTHON_VERSION=3.10
ARG DEBIAN_VERSION=bookworm
FROM python:$PYTHON_VERSION-$DEBIAN_VERSION AS builder

ARG GITHUB_ACCESS_TOKEN
RUN git config --global url."https://x-access-token:${GITHUB_ACCESS_TOKEN}@github.com/".insteadOf "https://github.com/"

RUN wget https://github.com/jgm/pandoc/releases/download/3.5/pandoc-3.5-linux-amd64.tar.gz && \
  tar -xvzf pandoc-3.5-linux-amd64.tar.gz && \
  mv pandoc-3.5/bin/* /usr/local/bin && \
  rm -rf pandoc-3.5*

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
  --mount=type=cache,target=/root/.cache/poetry,sharing=locked \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  --mount=type=bind,source=poetry.lock,target=poetry.lock \
  pip install -U pip && \
  pip install poetry==2.0.0 && \
  poetry config virtualenvs.create false && \
  poetry install --no-root

FROM python:$PYTHON_VERSION-slim-$DEBIAN_VERSION AS runner

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  apt-get update && apt-get install -y libpq-dev

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/pandoc /usr/local/bin/alembic /usr/local/bin/uvicorn /usr/local/bin/

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

ENTRYPOINT [ "/entrypoint.sh" ]
