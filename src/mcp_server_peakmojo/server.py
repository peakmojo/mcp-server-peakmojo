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
            # Job Tools
            types.Tool(
                name="get_jobs",
                description="List jobs with pagination support",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of jobs to return",
                            "default": 5
                        },
                        "next_token": {
                            "type": "string",
                            "description": "Pagination token"
                        }
                    }
                },
            ),
            types.Tool(
                name="create_jobs",
                description="Create one or more job listings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "jobs": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/JobCreateRequest"
                            }
                        }
                    },
                    "required": ["jobs"]
                },
            ),
            # Job Scenarios Tools
            types.Tool(
                name="search_job_scenarios",
                description="Search job scenarios",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    }
                },
            ),
            types.Tool(
                name="get_job_scenario",
                description="Get job scenario by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scenario_id": {
                            "type": "string",
                            "description": "Job scenario ID"
                        }
                    },
                    "required": ["scenario_id"]
                },
            ),
            # Application Tools
            types.Tool(
                name="get_applications",
                description="List job applications",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Filter by user ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of applications to return",
                            "default": 10
                        },
                        "next_token": {
                            "type": "string",
                            "description": "Pagination token"
                        }
                    }
                },
            ),
            types.Tool(
                name="create_application",
                description="Create a new job application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "application": {
                            "$ref": "#/components/schemas/ApplicationCreate"
                        }
                    },
                    "required": ["application"]
                },
            ),
            types.Tool(
                name="get_application",
                description="Get job application by ID",
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
            # Certificate Tools
            types.Tool(
                name="get_certificates",
                description="List certificates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of certificates to return",
                            "default": 10
                        },
                        "next_token": {
                            "type": "string",
                            "description": "Pagination token"
                        }
                    }
                },
            ),
            types.Tool(
                name="get_certificate",
                description="Get certificate by ID",
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
            types.Tool(
                name="add_user_skill",
                description="Add skill to user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "skill_id": {
                            "type": "string",
                            "description": "Skill ID"
                        }
                    },
                    "required": ["user_id", "skill_id"]
                },
            ),
            # Practice Tools
            types.Tool(
                name="get_practices",
                description="List practice sessions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of practices to return",
                            "default": 10
                        },
                        "next_token": {
                            "type": "string",
                            "description": "Pagination token"
                        }
                    }
                },
            ),
            types.Tool(
                name="get_practice",
                description="Get practice session by ID",
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
            # Persona Tools
            types.Tool(
                name="get_personas",
                description="List personas",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of personas to return",
                            "default": 10
                        },
                        "next_token": {
                            "type": "string",
                            "description": "Pagination token"
                        }
                    }
                },
            ),
            types.Tool(
                name="create_persona",
                description="Create a new persona",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "persona": {
                            "$ref": "#/components/schemas/PersonaCreate"
                        }
                    },
                    "required": ["persona"]
                },
            ),
            types.Tool(
                name="get_persona",
                description="Get persona by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "persona_id": {
                            "type": "string",
                            "description": "Persona ID"
                        }
                    },
                    "required": ["persona_id"]
                },
            ),
            # User Tools
            types.Tool(
                name="get_user_stats",
                description="Get user statistics",
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
            # Workspace Tools
            types.Tool(
                name="get_workspace_job_scenarios",
                description="Get job scenarios for workspace",
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
        ]

    @server.call_tool()
    async def handle_invoke_tool(name: str, inputs: Dict[str, Any]) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool invocations"""
        try:
            # Jobs
            if name == "get_jobs":
                params = {}
                if "limit" in inputs:
                    params["limit"] = inputs["limit"]
                if "next_token" in inputs:
                    params["next_token"] = inputs["next_token"]
                return peakmojo.execute_query('/v1/jobs/', params=params)
            elif name == "create_jobs":
                return peakmojo.execute_query('/v1/jobs/', method='POST', data=inputs["jobs"])
            
            # Job Scenarios
            elif name == "search_job_scenarios":
                return peakmojo.execute_query('/v1/job_scenarios/search', params={"query": inputs.get("query", "")})
            elif name == "get_job_scenario":
                return peakmojo.execute_query(f'/v1/job_scenarios/{inputs["scenario_id"]}')
            
            # Applications
            elif name == "get_applications":
                params = {}
                if "user_id" in inputs:
                    params["user_id"] = inputs["user_id"]
                if "limit" in inputs:
                    params["limit"] = inputs["limit"]
                if "next_token" in inputs:
                    params["next_token"] = inputs["next_token"]
                return peakmojo.execute_query('/v1/applications/', params=params)
            elif name == "create_application":
                return peakmojo.execute_query('/v1/applications/', method='POST', data=inputs["application"])
            elif name == "get_application":
                return peakmojo.execute_query(f'/v1/applications/{inputs["app_id"]}')
            
            # Certificates
            elif name == "get_certificates":
                params = {}
                if "limit" in inputs:
                    params["limit"] = inputs["limit"]
                if "next_token" in inputs:
                    params["next_token"] = inputs["next_token"]
                return peakmojo.execute_query('/v1/certificates/', params=params)
            elif name == "get_certificate":
                return peakmojo.execute_query(f'/v1/certificates/{inputs["certificate_id"]}')
            
            # Skills
            elif name == "get_user_skills":
                return peakmojo.execute_query(f'/v1/skills/{inputs["user_id"]}')
            elif name == "add_user_skill":
                return peakmojo.execute_query(
                    f'/v1/skills/{inputs["user_id"]}/add',
                    method='POST',
                    data={"skill_id": inputs["skill_id"]}
                )
            
            # Practices
            elif name == "get_practices":
                params = {}
                if "limit" in inputs:
                    params["limit"] = inputs["limit"]
                if "next_token" in inputs:
                    params["next_token"] = inputs["next_token"]
                return peakmojo.execute_query('/v1/practices/', params=params)
            elif name == "get_practice":
                return peakmojo.execute_query(f'/v1/practices/{inputs["practice_id"]}')
            
            # Personas
            elif name == "get_personas":
                params = {}
                if "limit" in inputs:
                    params["limit"] = inputs["limit"]
                if "next_token" in inputs:
                    params["next_token"] = inputs["next_token"]
                return peakmojo.execute_query('/v1/personas/peakmojo_personas', params=params)
            elif name == "create_persona":
                return peakmojo.execute_query('/v1/personas', method='POST', data=inputs["persona"])
            elif name == "get_persona":
                return peakmojo.execute_query(f'/v1/personas/{inputs["persona_id"]}')
            
            # User Stats
            elif name == "get_user_stats":
                return peakmojo.execute_query(f'/v1/users/{inputs["user_id"]}/stats')
            
            # Workspace
            elif name == "get_workspace_job_scenarios":
                return peakmojo.execute_query(f'/v1/workspaces/{inputs["workspace_id"]}/job_scenarios')
            
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
