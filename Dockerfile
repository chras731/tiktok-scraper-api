FROM python:3.12-slim

# Install system dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libasound2 \
    libxshmfence1 \
    libxss1 \
    libx11-xcb1 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and Chromium
RUN pip install playwright && playwright install --with-deps

# Copy all project files
COPY . .

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
