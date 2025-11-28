FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app/src
ENV CONFIG_FILE=/config/config.yaml

ENTRYPOINT ["python", "-m", "nina_mqtt_bridge", "-c", "/config/config.yaml"]
