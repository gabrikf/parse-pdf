# Backend image: the API (`python -m app.serve`) and the worker (`python -m app.worker.main`).
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /srv
RUN useradd --create-home --uid 10001 app

COPY pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt

COPY app ./app
RUN pip install --no-deps . && rm -rf build

FROM base AS runtime
USER app
EXPOSE 8000
CMD ["python", "-m", "app.serve"]

# Local OpenRouter stand-in for the e2e stack and the integration tests (never in production).
FROM base AS openrouter-stub
COPY stubs ./stubs
USER app
EXPOSE 8090
CMD ["uvicorn", "stubs.openrouter_stub:app", "--host", "0.0.0.0", "--port", "8090"]
