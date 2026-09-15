FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY volunteer_portal ./volunteer_portal
COPY pipeline ./pipeline
COPY README.md ./
COPY dataset ./dataset
COPY hybrid_model ./hybrid_model

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "volunteer_portal.app:app", "--host", "0.0.0.0", "--port", "8000"]
