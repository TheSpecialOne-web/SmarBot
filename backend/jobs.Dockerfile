ARG PYTHON_VERSION=3.10
ARG DEBIAN_VERSION=bookworm
FROM python:$PYTHON_VERSION-$DEBIAN_VERSION AS builder

ARG GITHUB_ACCESS_TOKEN
RUN git config --global url."https://x-access-token:${GITHUB_ACCESS_TOKEN}@github.com/".insteadOf "https://github.com/"

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
  apt-get update && apt-get install -y libpq-dev libreoffice-calc fonts-ipafont-gothic \
  libreoffice libreoffice-l10n-ja libreoffice-dmaths libreoffice-ogltrans libreoffice-writer2xhtml libreoffice-help-ja

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY . .

ENV PYTHONPATH=/app