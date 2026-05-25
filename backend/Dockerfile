FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN chmod +x prestart.sh

EXPOSE 8000

# Railway injects PORT; default 8000 for local Docker.
CMD ["bash", "-c", "bash prestart.sh && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
