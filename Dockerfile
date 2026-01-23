FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY step1.py .
COPY step2.py .
COPY step3.py .
COPY step4.py .
COPY srt_build.py .

# Create workspace directory
RUN mkdir -p /workspace

# Expose port
EXPOSE 8013

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8013"]
