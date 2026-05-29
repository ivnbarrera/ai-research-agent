"""Database MCP server — provides tools to query article database."""
import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.database.db_manager import DatabaseManager

server = Server("database-server")

db_manager: DatabaseManager = None


async def _init_db():
    global db_manager
    db_manager = DatabaseManager()
    await db_manager.initialize()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List database tools."""
    return [
        Tool(
            name="query_articles",
            description="Query articles from database with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Filter by source (optional, e.g., 'hackernews', 'rss')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of articles to return",
                        "default": 50,
                    },
                },
            },
        ),
        Tool(
            name="search_articles",
            description="Search articles by keyword in title or summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (searches in title and summary)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_sources",
            description="Get list of all available sources in database",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute database tool."""
    global db_manager
    if not db_manager:
        await _init_db()

    if name == "query_articles":
        articles = await db_manager.query_articles(
            source=arguments.get("source"),
            limit=arguments.get("limit", 50),
        )
        result = {"total": len(articles), "articles": articles[:10]}
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "search_articles":
        query = arguments["query"].lower()
        limit = arguments.get("limit", 20)

        all_articles = await db_manager.query_articles(limit=1000)

        matches = [
            article
            for article in all_articles
            if query in article["title"].lower()
            or query in article.get("summary", "").lower()
        ]

        result = {
            "total": len(matches),
            "query": query,
            "articles": matches[:limit],
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_sources":
        articles = await db_manager.query_articles(limit=1000)
        sources = list({a["source"] for a in articles})
        result = {"sources": sources, "total": len(sources)}
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run database MCP server."""
    await _init_db()
    print("🗄️  Database MCP Server starting...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
