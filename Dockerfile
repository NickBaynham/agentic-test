FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PDM_CHECK_UPDATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PDM_USE_VENV=true

RUN pip install --no-cache-dir "pdm>=2.25,<3"

COPY pyproject.toml pdm.lock README.md ./
COPY src ./src

RUN pdm sync --prod --no-editable

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "agentic_test.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
