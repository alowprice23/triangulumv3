# Use a base image with Python and Node.js pre-installed for convenience.
# A specific version is chosen for reproducibility.
FROM python:3.11-slim as python-base

# Install Node.js and npm
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python test dependencies globally in the image
RUN pip install --no-cache-dir pytest pytest-json-report

# Install JavaScript test dependencies globally in the image
# This allows us to run jest without an `npm install` step in the sandbox
RUN npm install -g jest

# Set a working directory
WORKDIR /app

# The entrypoint can be a simple shell, as the test_runner will pass
# the full command to execute.
ENTRYPOINT ["/bin/sh", "-c"]
