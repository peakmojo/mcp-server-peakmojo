# PeakMojo Server

[![Docker Hub](https://img.shields.io/docker/v/peakmojo/mcp-server-peakmojo?label=Docker%20Hub)](https://hub.docker.com/r/peakmojo/mcp-server-peakmojo)

A Python server implementation for integrating with the PeakMojo API.

## Features

- Full integration with PeakMojo API endpoints
- Bearer token authentication
- Resource and tool-based access to PeakMojo functionality
- Automatic fallback to mock responses during development

## Installation

```bash
pip install mcp-server-peakmojo
```

## Configuration

The server requires the following environment variables:

- `PEAKMOJO_API_KEY`: Your PeakMojo API key for authentication
- `PEAKMOJO_BASE_URL` (optional): PeakMojo API base URL (defaults to https://api.staging.readymojo.com)

You can also configure these via command line arguments:

```bash
python -m mcp_server_peakmojo --api-key YOUR_API_KEY --base-url YOUR_BASE_URL
```

## Available Resources

The server provides access to the following PeakMojo resources:

- Users (`peakmojo://users`)
- Personas (`peakmojo://personas`, `peakmojo://personas/tags`, `peakmojo://personas/search`)
- Scenarios (`peakmojo://scenarios`)
- Job Scenarios (`peakmojo://job_scenarios`)
- Jobs (`peakmojo://jobs`)
- Applications (`peakmojo://applications`)
- Practices (`peakmojo://practices`)
- Skills (`peakmojo://skills`)
- Certificates (`peakmojo://certificates`)

## Available Tools

The server provides the following tools for interacting with the PeakMojo API:

### User Management
- `get_peakmojo_users`: Get list of all users
- `get_peakmojo_user`: Get user details by ID
- `get_peakmojo_user_stats`: Get user statistics
- `update_peakmojo_user_stats`: Update user statistics

### Persona Management
- `get_peakmojo_personas`: Get list of personas
- `get_peakmojo_persona_tags`: Get persona tags
- `search_peakmojo_personas`: Search for personas
- `create_peakmojo_persona`: Create a new persona

### Scenario Management
- `get_peakmojo_scenarios`: Get list of scenarios
- `create_peakmojo_job_scenario`: Create a new job scenario

### Workspace Management
- `get_workspace_personas`: Get personas for a workspace

### Job Management
- `get_job`: Get job details

### Application Management
- `get_application`: Get application details

### Practice Management
- `get_practice_messages`: Get practice messages

### Skill Management
- `get_user_skills`: Get user skills

### Certificate Management
- `get_certificates`: Get list of certificates
- `get_certificate_skills`: Get skills for a certificate
- `issue_user_certificate`: Issue a certificate to a user
- `add_certificate_skill_courses`: Add courses to a certificate skill

## Development

During development, if the API is not accessible, the server will automatically fall back to mock responses for each endpoint. This allows for development and testing without requiring a live API connection.

## Error Handling

The server implements comprehensive error handling:
- Invalid API keys are logged with warnings
- Failed API requests fall back to mock responses
- HTTP errors are properly caught and logged
- All errors are returned as JSON responses with appropriate error messages

## Docker Support

### Prerequisites

The Docker image is built for multiple platforms:
- Linux/amd64
- Linux/arm64
- Linux/arm/v7

### Option 1: Pull from Docker Hub

```bash
docker pull buryhuang/mcp-server-peakmojo:latest
```

### Option 2: Build Locally

```bash
docker build -t mcp-server-peakmojo .
```

### Running the Container

Basic usage with API key:
```bash
docker run \
  -e PEAKMOJO_API_KEY=your_api_key_here \
  -e PEAKMOJO_BASE_URL=https://api.staging.readymojo.com \
  buryhuang/mcp-server-peakmojo:latest
```

### Cross-Platform Publishing

To publish the Docker image for multiple platforms:

1. Create a new builder instance (if you haven't already):
   ```bash
   docker buildx create --use
   ```

2. Build and push the image for multiple platforms:
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t peakmojo/mcp-server-peakmojo:latest --push .
   ```

3. Verify the image is available for the specified platforms:
   ```bash
   docker buildx imagetools inspect peakmojo/mcp-server-peakmojo:latest
   ```

### Usage with Claude Desktop

Configure the MCP server in your Claude Desktop settings:

```json
{
  "mcpServers": {
    "peakmojo": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "PEAKMOJO_API_KEY=your_api_key_here",
        "-e",
        "PEAKMOJO_BASE_URL=https://api.staging.readymojo.com",
        "peakmojo/mcp-server-peakmojo:latest"
      ]
    }
  }
}
```

### Example running from source

If you want to run directly from the source code:

```json
{
  "mcpServers": {
    "peakmojo": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server_peakmojo",
        "--api-key",
        "your_api_key_here",
        "--base-url",
        "https://api.staging.readymojo.com"
      ]
    }
  }
}
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
