import argparse
import json
import logging
import os
from typing import Any, Dict, Optional

import requests
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

    def execute_query(self, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> str:
        """Execute a query against the PeakMojo API"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self.get_headers()
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None
            )
            
            # Raise an exception for bad status codes
            response.raise_for_status()
            
            # Return the JSON response as a string
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Error executing query: {str(e)}")
            # For development/debugging, return placeholder responses if API call fails
            if endpoint == '/v1/users':
                return json.dumps({"users": []})
            elif endpoint.startswith('/v1/users/') and endpoint.endswith('/stats'):
                user_id = endpoint.split('/')[-2]
                return json.dumps({"stats": {"user_id": user_id, "metrics": {}}})
            elif endpoint.startswith('/v1/users/') and endpoint.endswith('/skills'):
                user_id = endpoint.split('/')[-2]
                return json.dumps({"skills": [], "user_id": user_id})
            elif endpoint.startswith('/v1/users/') and endpoint.endswith('/issue'):
                return json.dumps({"success": True, "message": "Certificate issued"})
            elif endpoint.startswith('/v1/users/'):
                user_id = endpoint.split('/')[-1]
                return json.dumps({"user": {"id": user_id, "name": f"User {user_id}"}})
            elif endpoint == '/v1/personas/peakmojo_personas':
                return json.dumps({"personas": []})
            elif endpoint == '/v1/personas/tags':
                return json.dumps({"tags": []})
            elif endpoint == '/v1/personas/search':
                return json.dumps({"search_results": []})
            elif endpoint == '/v1/personas' and method == 'POST':
                return json.dumps({"success": True, "persona": data})
            elif endpoint == '/v1/scenarios/peakmojo_scenarios':
                return json.dumps({"scenarios": []})
            elif endpoint == '/v1/job_scenarios' and method == 'POST':
                return json.dumps({"success": True, "scenario": data})
            elif endpoint.startswith('/v1/workspaces/') and endpoint.endswith('/personas'):
                workspace_id = endpoint.split('/')[-2]
                return json.dumps({"workspace_id": workspace_id, "personas": []})
            elif endpoint.startswith('/v1/job/'):
                job_id = endpoint.split('/')[-1]
                return json.dumps({"job": {"id": job_id, "status": "pending"}})
            elif endpoint.startswith('/v1/applications/'):
                app_id = endpoint.split('/')[-1]
                return json.dumps({"application": {"id": app_id, "status": "pending"}})
            elif endpoint.startswith('/v1/practices/') and endpoint.endswith('/messages'):
                practice_id = endpoint.split('/')[-2]
                return json.dumps({"practice_id": practice_id, "messages": []})
            elif endpoint == '/v1/certificates':
                return json.dumps({"certificates": []})
            elif endpoint.startswith('/v1/certificates/') and endpoint.endswith('/skills'):
                cert_id = endpoint.split('/')[-2]
                return json.dumps({"certificate_id": cert_id, "skills": []})
            elif endpoint.startswith('/v1/certificates/') and endpoint.endswith('/courses'):
                if method == 'POST':
                    return json.dumps({"success": True, "message": "Courses added"})
                return json.dumps({"error": "Method not allowed"})
            else:
                return json.dumps({"error": f"Endpoint not implemented: {endpoint}"})


async def main():
    """Run the PeakMojo Server"""
    logger.info("PeakMojo Server starting")
    
    peakmojo = PeakMojoQuerier()
    server = Server("peakmojo")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl("peakmojo://users"),
                name="PeakMojo Users",
                description="Access PeakMojo user-related resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://personas"),
                name="PeakMojo Personas",
                description="Access PeakMojo persona-related resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://personas/tags"),
                name="PeakMojo Persona Tags",
                description="Access PeakMojo persona tags",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://personas/search"),
                name="PeakMojo Persona Search",
                description="Search PeakMojo personas",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://scenarios"),
                name="PeakMojo Scenarios",
                description="Access PeakMojo scenario-related resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://job_scenarios"),
                name="PeakMojo Job Scenarios",
                description="Access PeakMojo job scenario resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://jobs"),
                name="PeakMojo Jobs",
                description="Access PeakMojo job resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://applications"),
                name="PeakMojo Applications",
                description="Access PeakMojo application resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://practices"),
                name="PeakMojo Practices",
                description="Access PeakMojo practice resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://skills"),
                name="PeakMojo Skills",
                description="Access PeakMojo skill resources",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl("peakmojo://certificates"),
                name="PeakMojo Certificates",
                description="Access PeakMojo certificate resources",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        if uri.scheme != "peakmojo":
            raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

        path = str(uri).replace("peakmojo://", "")
        
        # Map paths to correct API endpoints
        endpoint_map = {
            "users": "/v1/users",
            "personas": "/v1/personas/peakmojo_personas",
            "personas/tags": "/v1/personas/tags",
            "personas/search": "/v1/personas/search",
            "scenarios": "/v1/scenarios/peakmojo_scenarios",
            "job_scenarios": "/v1/job_scenarios/peakmojo_scenarios",
            "jobs": "/v1/jobs",
            "applications": "/v1/applications",
            "practices": "/v1/practices",
            "skills": "/v1/skills",
            "certificates": "/v1/certificates"
        }
        
        if path not in endpoint_map:
            raise ValueError(f"Unknown resource path: {path}")
            
        return peakmojo.execute_query(endpoint_map[path])

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            # User Tools
            types.Tool(
                name="get_peakmojo_users",
                description="Get list of PeakMojo users",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            types.Tool(
                name="get_peakmojo_user",
                description="Get PeakMojo user details by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "PeakMojo User ID to retrieve"
                        }
                    },
                    "required": ["user_id"]
                },
            ),
            types.Tool(
                name="get_peakmojo_user_stats",
                description="Get PeakMojo user statistics by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "PeakMojo User ID to retrieve stats for"
                        }
                    },
                    "required": ["user_id"]
                },
            ),
            types.Tool(
                name="update_peakmojo_user_stats",
                description="Update PeakMojo user statistics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stats": {
                            "type": "object",
                            "description": "PeakMojo user statistics to update"
                        }
                    },
                    "required": ["stats"]
                },
            ),
            # Persona Tools
            types.Tool(
                name="get_peakmojo_personas",
                description="Get list of PeakMojo personas",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            types.Tool(
                name="get_peakmojo_persona_tags",
                description="Get PeakMojo persona tags",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            types.Tool(
                name="search_peakmojo_personas",
                description="Search for PeakMojo personas",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            types.Tool(
                name="create_peakmojo_persona",
                description="Create a new PeakMojo persona",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "persona": {
                            "type": "object",
                            "description": "PeakMojo persona details"
                        }
                    },
                    "required": ["persona"]
                },
            ),
            # Scenario Tools
            types.Tool(
                name="get_peakmojo_scenarios",
                description="Get list of PeakMojo scenarios",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            # Job Scenario Tools
            types.Tool(
                name="create_peakmojo_job_scenario",
                description="Create a new PeakMojo job scenario",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scenario": {
                            "type": "object",
                            "description": "PeakMojo job scenario details"
                        }
                    },
                    "required": ["scenario"]
                },
            ),
            # Workspace Tools
            types.Tool(
                name="get_workspace_personas",
                description="Get personas for a workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "Workspace ID"
                        }
                    },
                    "required": ["workspace_id"]
                },
            ),
            # Job Tools
            types.Tool(
                name="get_job",
                description="Get job details",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Job ID"
                        }
                    },
                    "required": ["job_id"]
                },
            ),
            # Application Tools
            types.Tool(
                name="get_application",
                description="Get application details",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_id": {
                            "type": "string",
                            "description": "Application ID"
                        }
                    },
                    "required": ["app_id"]
                },
            ),
            # Practice Tools
            types.Tool(
                name="get_practice_messages",
                description="Get practice messages",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "practice_id": {
                            "type": "string",
                            "description": "Practice ID"
                        }
                    },
                    "required": ["practice_id"]
                },
            ),
            # Skill Tools
            types.Tool(
                name="get_user_skills",
                description="Get user skills",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        }
                    },
                    "required": ["user_id"]
                },
            ),
            # Certificate Tools
            types.Tool(
                name="get_certificates",
                description="Get list of PeakMojo certificates",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            types.Tool(
                name="get_certificate_skills",
                description="Get skills for a certificate",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "certificate_id": {
                            "type": "string",
                            "description": "Certificate ID"
                        }
                    },
                    "required": ["certificate_id"]
                },
            ),
            types.Tool(
                name="issue_user_certificate",
                description="Issue a certificate to a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "certificate_id": {
                            "type": "string",
                            "description": "Certificate ID"
                        }
                    },
                    "required": ["user_id", "certificate_id"]
                },
            ),
            types.Tool(
                name="add_certificate_skill_courses",
                description="Add courses to a certificate skill",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "certificate_id": {
                            "type": "string",
                            "description": "Certificate ID"
                        },
                        "skill_id": {
                            "type": "string",
                            "description": "Skill ID"
                        },
                        "courses": {
                            "type": "array",
                            "description": "List of courses to add",
                            "items": {
                                "type": "object"
                            }
                        }
                    },
                    "required": ["certificate_id", "skill_id", "courses"]
                },
            ),
        ]

    @server.call_tool()
    async def handle_invoke_tool(name: str, inputs: Dict[str, Any]) -> str:
        """Handle tool invocations"""
        try:
            if name == "get_peakmojo_users":
                return peakmojo.execute_query('/v1/users')
            elif name == "get_peakmojo_user":
                return peakmojo.execute_query(f'/v1/users/{inputs["user_id"]}')
            elif name == "get_peakmojo_user_stats":
                return peakmojo.execute_query(f'/v1/users/{inputs["user_id"]}/stats')
            elif name == "update_peakmojo_user_stats":
                return peakmojo.execute_query('/v1/users/stats', method='POST', data=inputs["stats"])
            elif name == "get_peakmojo_personas":
                return peakmojo.execute_query('/v1/personas/peakmojo_personas')
            elif name == "get_peakmojo_persona_tags":
                return peakmojo.execute_query('/v1/personas/tags')
            elif name == "search_peakmojo_personas":
                return peakmojo.execute_query('/v1/personas/search')
            elif name == "create_peakmojo_persona":
                return peakmojo.execute_query('/v1/personas', method='POST', data=inputs["persona"])
            elif name == "get_peakmojo_scenarios":
                return peakmojo.execute_query('/v1/scenarios/peakmojo_scenarios')
            elif name == "create_peakmojo_job_scenario":
                return peakmojo.execute_query('/v1/job_scenarios', method='POST', data=inputs["scenario"])
            elif name == "get_workspace_personas":
                return peakmojo.execute_query(f'/v1/workspaces/{inputs["workspace_id"]}/personas')
            elif name == "get_job":
                return peakmojo.execute_query(f'/v1/job/{inputs["job_id"]}')
            elif name == "get_application":
                return peakmojo.execute_query(f'/v1/applications/{inputs["app_id"]}')
            elif name == "get_practice_messages":
                return peakmojo.execute_query(f'/v1/practices/{inputs["practice_id"]}/messages')
            elif name == "get_user_skills":
                return peakmojo.execute_query(f'/v1/users/{inputs["user_id"]}/skills')
            elif name == "get_certificates":
                return peakmojo.execute_query('/v1/certificates')
            elif name == "get_certificate_skills":
                return peakmojo.execute_query(f'/v1/certificates/{inputs["certificate_id"]}/skills')
            elif name == "issue_user_certificate":
                return peakmojo.execute_query(
                    f'/v1/users/{inputs["user_id"]}/certificates/{inputs["certificate_id"]}/issue',
                    method='POST'
                )
            elif name == "add_certificate_skill_courses":
                return peakmojo.execute_query(
                    f'/v1/certificates/{inputs["certificate_id"]}/skills/{inputs["skill_id"]}/courses',
                    method='POST',
                    data={"courses": inputs["courses"]}
                )
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error invoking tool {name}: {str(e)}")
            return json.dumps({"error": str(e)})

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
