FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Copy requirements first
COPY api/requirements.txt ./requirements.txt

# Copy pre-downloaded wheels
COPY api/wheels/ ./wheels/

# Install from local wheels (no internet needed)
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy model directly from GitHub release
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

COPY api/ ./api/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]