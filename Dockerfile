FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    tesseract-ocr \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY setup/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Install extra dependencies added manually
RUN pip install --no-cache-dir opencv-python openai feedparser praw redis pytesseract pillow

# Copy source code
COPY . .

# Install the package in editable mode or just add to pythonpath
ENV PYTHONPATH=/app/src

# Default command (can be overridden)
CMD ["uvicorn", "webis.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
