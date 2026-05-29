"""Simple MCP client for testing."""
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_hello_server():
    """Test hello world MCP server."""
    print("🔌 Connecting to hello-world server...")

    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp_servers/hello_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"\n📋 Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            print(f"\n🔧 Calling 'greet' tool...")
            result = await session.call_tool("greet", {"name": "Alice"})
            print(f"   Result: {result.content[0].text}")

            print(f"\n🔧 Calling 'add' tool...")
            result = await session.call_tool("add", {"a": 5, "b": 3})
            print(f"   Result: {result.content[0].text}")

            print("\n✅ MCP communication working!")


if __name__ == "__main__":
    asyncio.run(test_hello_server())
