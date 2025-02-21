# Use Python base image
FROM python:3.10-slim-bookworm

# Install the project into `/app`
WORKDIR /app

# Copy the entire project
COPY . /app

# Install dependencies first for better caching
RUN pip install --no-cache-dir mcp pydantic requests

# Install the package in development mode
RUN pip install -e .

# Run the server
ENTRYPOINT ["python", "-m", "mcp_server_peakmojo.server"]