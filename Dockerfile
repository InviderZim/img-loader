FROM python:3.14-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app.py .
COPY static/ static/

RUN mkdir -p /images /logs

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "app.py"]