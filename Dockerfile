FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY static/ static/

RUN mkdir -p /images /logs

EXPOSE 8000

CMD ["python", "app.py"]