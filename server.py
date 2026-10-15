try:
    from mcp.server.mcpserver.context import Context
    from mcp.server.mcpserver.server import MCPServer as FastMCP
except ModuleNotFoundError:
    from mcp.server.fastmcp import Context, FastMCP
import hashlib

# Initialize the FastMCP server
mcp = FastMCP("ExamServer")

@mcp.tool()
async def solve_challenge(ctx: Context) -> str:
    # Access the raw HTTP request headers via the underlying Starlette request object
    headers = getattr(ctx, "headers", None)
    if headers is None:
        request_context = ctx.request_context
        if request_context is None:
            raise RuntimeError("Request headers are unavailable outside an active request")
        headers = request_context.request.headers
    
    # Normalize header keys to lowercase for case-insensitive lookup
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    # Extract the challenge from the header
    challenge = headers_lower.get("x-exam-challenge", "")
    
    # Normalized email as per requirements (trimmed and lowercased)
    normalized_email = "24f3003132@ds.study.iitm.ac.in"
    
    # Compute SHA-256 of "${challenge}:${normalizedEmail}"
    data = f"{challenge}:{normalized_email}"
    hash_obj = hashlib.sha256(data.encode('utf-8'))
    
    # Return the first 16 lowercase hex characters
    return hash_obj.hexdigest()[:16]

if __name__ == "__main__":
    # Run the server with streamable-http transport on all network interfaces
    mcp.run(host="0.0.0.0", port=8000, transport="streamable-http")