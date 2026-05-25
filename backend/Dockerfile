FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN chmod +x prestart.sh start.sh

EXPOSE 8000

CMD ["bash", "start.sh"]
