FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 \
    build-essential libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libxss1 libappindicator3-1 \
    libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libgbm1 libasound2 \
    chromium chromium-driver \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Chromium as default
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="${PATH}:/usr/bin"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
