FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=0

WORKDIR /app

# 🔥 ALL required system deps (including libcups2)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libcups2 \
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libxcomposite1 \
    libxfixes3 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🔥 Browser install
RUN playwright install chromium

COPY app.py .

EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-t", "120", "-b", "0.0.0.0:5000", "app:app"]

