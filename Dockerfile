# Dockerfile
FROM python:3.12-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip gnupg2 curl && \
    apt-get install -y chromium chromium-driver && \
    pip install --upgrade pip

# Set env variables for headless Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
