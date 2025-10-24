# Python base image (Alpine to install wkhtmltopdf reliably)
FROM python:3.11-alpine

# Install wkhtmltopdf and fonts on Alpine
RUN apk add --no-cache \
      wkhtmltopdf \
      ttf-dejavu \
      fontconfig \
      ca-certificates

# Set workdir
WORKDIR /app

# Copy dependency manifest
COPY requirements.txt ./

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app ./app

# Environment
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    FLASK_ENV=production \
    WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf

# Expose web port
EXPOSE 8000

# Start the server with gunicorn
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:8000", "app.main:app"]
