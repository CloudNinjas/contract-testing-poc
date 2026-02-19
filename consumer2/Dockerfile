FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e ".[test]"

# Copy source code
COPY . .

CMD ["pytest", "tests/", "-v"]
