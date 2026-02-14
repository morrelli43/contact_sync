FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

LABEL org.opencontainers.image.source=https://github.com/morrelli43/contact_sync
LABEL org.opencontainers.image.description="Contact Sync Service"
LABEL org.opencontainers.image.licenses=MIT

# Expose the Flask port
EXPOSE 7173

ENTRYPOINT ["python", "main.py"]
