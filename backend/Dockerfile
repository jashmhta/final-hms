# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && apt-get install -y build-essential libpq-dev python3-setuptools python3-pip && rm -rf /var/lib/apt/lists/* && pip install --upgrade pip setuptools wheel

COPY requirements-minimal.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

# Copy local packages to site-packages
RUN cp -r /app/libs/* /usr/local/lib/python3.12/site-packages/

ENV DJANGO_SETTINGS_MODULE=hms.settings

RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m appuser
# USER appuser  # Temporarily run as root for debugging

EXPOSE 8000
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
ENV OTEL_METRICS_EXPORTER=none
ENV PYTHONPATH=/app
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
