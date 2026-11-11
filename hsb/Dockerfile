FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip install --no-cache-dir fastapi uvicorn requests pydantic psycopg2-binary

COPY . /app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "hsb.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "75"]
