FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias esenciales
RUN pip install --no-cache-dir fastapi uvicorn requests pydantic

COPY . /app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "hsb.main:app", "--host", "0.0.0.0", "--port", "8000"]
