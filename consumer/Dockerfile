FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pact
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/

# Install dependencies
RUN pip install --no-cache-dir -e ".[test]"

# Create pacts directory
RUN mkdir -p pacts

# Default command - run contract tests
CMD ["pytest", "tests/", "-v", "--tb=short"]
