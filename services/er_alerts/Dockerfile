FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 9016
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
ENV OTEL_METRICS_EXPORTER=none
CMD ["sh", "-c", "opentelemetry-instrument --traces_exporter otlp --service_name er-alerts uvicorn app.main:app --host 0.0.0.0 --port 9016"]