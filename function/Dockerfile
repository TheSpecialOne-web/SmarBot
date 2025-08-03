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

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

COPY . .

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "jobs.main"]
