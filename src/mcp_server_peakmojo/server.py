import argparse
import json
import logging
import os
from typing import Any, Dict, Optional

import requests
import yaml
from mcp.server import Server
import mcp.types as types
import mcp.server.stdio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("peakmojo_server")


def parse_arguments() -> argparse.Namespace:
    """Use argparse to allow values to be set as CLI switches
    or environment variables
    """
    parser = argparse.ArgumentParser(description='PeakMojo Server')
    parser.add_argument('--api-key', help='PeakMojo API key', default=os.environ.get('PEAKMOJO_API_KEY'))
    parser.add_argument('--base-url', help='PeakMojo API base URL', default=os.environ.get('PEAKMOJO_BASE_URL', 'https://api.staging.readymojo.com'))
    return parser.parse_args()


class PeakMojoQuerier:
    def __init__(self):
        """Initialize PeakMojo API client"""
        args = parse_arguments()
        self.api_key = args.api_key
        self.base_url = args.base_url

        if not self.api_key:
            logger.warning("PeakMojo API key not found in environment variables")

    def get_headers(self) -> dict:
        """Get request headers with Bearer token"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def execute_query(self, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Execute a query against the PeakMojo API and return response in YAML format"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self.get_headers()
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                params=params if params else None
            )
            
            # Raise an exception for bad status codes
            response.raise_for_status()
            
            # Parse JSON response and convert to YAML
            json_response = response.json()
            yaml_response = yaml.dump(json_response, sort_keys=False, allow_unicode=True)
            
            return [types.TextContent(type="text", text=yaml_response)]

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            error_response = {"error": str(e)}
            yaml_response = yaml.dump(error_response, sort_keys=False, allow_unicode=True)
            return [types.TextContent(type="text", text=yaml_response)]


async def main():
    """Run the PeakMojo Server"""
    logger.info("PeakMojo Server starting")
    
    peakmojo = PeakMojoQuerier()
    server = Server("peakmojo")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl("peakmojo://api"),
                name="PeakMojo API",
                description="Access any PeakMojo API endpoint",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        if uri.scheme != "peakmojo":
            raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

        path = str(uri).replace("peakmojo://", "")
        if path != "api":
            raise ValueError(f"Unknown resource path: {path}")
            
        return peakmojo.execute_query("/")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="peakmojo_make_api_request",
                description="Make a request to any PeakMojo API endpoint. Use the API documentation at /api/docs/categories to discover available endpoints.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "endpoint": {
                            "type": "string",
                            "description": "The API endpoint to call (e.g. '/v1/users' or '/api/docs/categories')"
                        },
                        "method": {
                            "type": "string",
                            "description": "HTTP method (GET, POST, PUT, DELETE, etc)",
                            "default": "GET",
                            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                        },
                        "params": {
                            "type": "object",
                            "description": "Query parameters to include in the request",
                            "additionalProperties": True
                        },
                        "data": {
                            "type": "object",
                            "description": "Request body for POST/PUT/PATCH requests",
                            "additionalProperties": True
                        }
                    },
                    "required": ["endpoint"]
                },
            ),
        ]

    @server.call_tool()
    async def handle_invoke_tool(name: str, inputs: Dict[str, Any]) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool invocations"""
        try:
            if name == "peakmojo_make_api_request":
                endpoint = inputs["endpoint"]
                method = inputs.get("method", "GET")
                params = inputs.get("params", {})
                data = inputs.get("data", {})
                
                # Ensure endpoint starts with /
                if not endpoint.startswith("/"):
                    endpoint = f"/{endpoint}"
                    
                return peakmojo.execute_query(
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    data=data
                )
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Error invoking tool {name}: {str(e)}")
            return [types.TextContent(type="text", text=yaml.dump({"error": str(e)}, sort_keys=False, allow_unicode=True))]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="peakmojo",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
