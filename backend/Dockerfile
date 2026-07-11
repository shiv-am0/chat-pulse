FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0

COPY . .

RUN mkdir -p staticfiles

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
