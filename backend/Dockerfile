# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV DJANGO_SETTINGS_MODULE=hms.settings

RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8000
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
ENV OTEL_METRICS_EXPORTER=none
ENV PYTHONPATH=/app/libs
CMD ["sh", "-c", "python manage.py migrate && opentelemetry-instrument --traces_exporter otlp --service_name backend gunicorn hms.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60"]
