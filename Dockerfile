FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

COPY app/ ./app/

EXPOSE 5049

ENV PATH="/app/.venv/bin:$PATH"

CMD xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
    uvicorn app.app:app --host 0.0.0.0 --port 5049
