# Use a slim Python image
FROM python:3.11-slim

# System deps for OCR + PDF rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
  && rm -rf /var/lib/apt/lists/*

# App setup
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Render provides PORT
ENV PYTHONUNBUFFERED=1

CMD ["bash", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
