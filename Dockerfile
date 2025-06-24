FROM python:3.12-slim

# Install Chrome & dependencies
RUN apt-get update && apt-get install -y     wget     unzip     gnupg     curl     ca-certificates     fonts-liberation     libappindicator3-1     libasound2     libatk-bridge2.0-0     libatk1.0-0     libcups2     libdbus-1-3     libgdk-pixbuf2.0-0     libnspr4     libnss3     libx11-xcb1     libxcomposite1     libxdamage1     libxrandr2     xdg-utils     --no-install-recommends &&     rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb &&     apt-get update &&     apt-get install -y ./chrome.deb &&     rm chrome.deb

# Install Chromedriver
RUN CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) &&     curl -sSL https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip -o chromedriver.zip &&     unzip chromedriver.zip -d /usr/local/bin/ &&     rm chromedriver.zip

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]