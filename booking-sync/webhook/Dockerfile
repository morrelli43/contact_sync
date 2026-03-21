# Dockerfile for Square webhook receiver
FROM python:3.10-slim
WORKDIR /app
COPY ../main.py ../booking_model.py ../square_booking_connector.py ../google_calendar_connector.py ./
COPY requirements.txt ./
COPY app.py ./
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
