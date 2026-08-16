# Cloud Run / local API image (repo root context)
FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY apps/api /app/apps/api
COPY data /app/data

WORKDIR /app/apps/api
ENV PYTHONPATH=/app/apps/api
ENV BR_DATA_MODE=fixtures
ENV PORT=8080

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
