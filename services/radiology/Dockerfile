# syntax=docker/dockerfile:1
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini ./alembic.ini
COPY alembic /app/alembic
COPY . /app
EXPOSE 9012
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
ENV OTEL_METRICS_EXPORTER=none
CMD sh -c "alembic upgrade head && opentelemetry-instrument --traces_exporter otlp --service_name radiology uvicorn app.main:app --host 0.0.0.0 --port 9012"
