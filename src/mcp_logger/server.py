import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from .db import write_log, read_logs, search_logs


server = Server("mcp-logger")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="log_write",
            description="Write a log entry",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Log message"},
                    "level": {
                        "type": "string",
                        "enum": ["debug", "info", "warning", "error"],
                        "default": "info",
                    },
                    "repo": {"type": "string", "description": "Repository name"},
                    "source": {
                        "type": "string",
                        "enum": ["agent", "application"],
                        "default": "application",
                    },
                    "metadata": {
                        "type": "string",
                        "description": "Optional JSON metadata",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="log_read",
            description="Read latest log entries",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of entries",
                    },
                    "level": {"type": "string", "description": "Filter by level"},
                    "repo": {"type": "string", "description": "Filter by repository"},
                },
            },
        ),
        Tool(
            name="log_search",
            description="Search log entries",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search term"},
                    "level": {"type": "string", "description": "Filter by level"},
                    "repo": {"type": "string", "description": "Filter by repository"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["search"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "log_write":
        result = write_log(
            message=arguments["message"],
            level=arguments.get("level", "info"),
            repo=arguments.get("repo"),
            source=arguments.get("source", "application"),
            metadata=arguments.get("metadata"),
        )
        return [TextContent(type="text", text=f"Logged entry {result}")]
    elif name == "log_read":
        logs = read_logs(
            n=arguments.get("n", 10),
            level=arguments.get("level"),
            repo=arguments.get("repo"),
        )
        return [TextContent(type="text", text=json.dumps(logs, indent=2))]
    elif name == "log_search":
        logs = search_logs(
            search=arguments["search"],
            level=arguments.get("level"),
            repo=arguments.get("repo"),
            limit=arguments.get("limit", 50),
        )
        return [TextContent(type="text", text=json.dumps(logs, indent=2))]
    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options(),
        )


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
