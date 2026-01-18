# Dockerfile pour Backend (FastAPI)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including Java 21 for Android build dependencies)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    openjdk-21-jdk \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4