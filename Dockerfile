FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config/ config/
COPY modules/ modules/
COPY server/ server/
COPY data/ data/
COPY .env.example .env

EXPOSE 8000

CMD ["python", "server/main_api.py"]
