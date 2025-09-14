# syntax=docker/dockerfile:1
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini ./alembic.ini
COPY alembic /app/alembic
COPY . /app
EXPOSE 9008
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 9008
