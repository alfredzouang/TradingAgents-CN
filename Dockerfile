# ----------- Builder Stage -----------
FROM python:3.10-bullseye AS builder

WORKDIR /app

# Install build dependencies and runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        wkhtmltopdf \
        xvfb \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        fonts-liberation \
        pandoc \
        procps \
        curl \
        ca-certificates

# Install Python dependencies in a clean target directory
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# Copy application code (for possible build steps, e.g. static assets)
COPY . .

# ----------- Final Stage -----------
FROM python:3.10-slim AS final

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Install only runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wkhtmltopdf \
        xvfb \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        fonts-liberation \
        pandoc \
        procps \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code (ensure all source is present)
COPY --from=builder /app /app

# Xvfb startup script
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x24 -ac +extension GLX &\nexport DISPLAY=:99\nexec "$@"' > /usr/local/bin/start-xvfb.sh \
    && chmod +x /usr/local/bin/start-xvfb.sh

RUN find /app

EXPOSE 8501

CMD ["bash", "-c", "export PYTHONPATH=/app && python -m streamlit run web/app.py --server.address=0.0.0.0 --server.port=8501"]
