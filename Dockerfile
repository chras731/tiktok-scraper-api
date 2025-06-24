FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install system dependencies
RUN apt-get update && \
    apt-get install -y wget curl gnupg2 unzip fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
    libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxrandr2 xdg-utils libgbm1 libvulkan1 libgtk-3-0

# Install Chrome 126 manually (known to work)
RUN wget -O chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_126.0.6478.126-1_amd64.deb && \
    apt install -y ./chrome.deb && \
    rm chrome.deb

# Install matching Chromedriver 126
RUN wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/126.0.6478.126/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY . .

# Launch app
CMD ["python", "main.py"]
