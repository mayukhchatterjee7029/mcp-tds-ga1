import hashlib
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()
EMAIL = "24f3003132@ds.study.iitm.ac.in".strip().lower()

TOOL = {
    "name": "solve_challenge",
    "description": "Returns the exam challenge response derived from request headers.",
    "inputSchema": {"type": "object", "properties": {}},
}

def rpc_result(id_, result):
    return JSONResponse({"jsonrpc": "2.0", "id": id_, "result": result})

def rpc_error(id_, code, msg):
    return JSONResponse({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": msg}})

@app.get("/mcp")
async def mcp_get():
    return Response(status_code=405, headers={"Allow": "POST"})

@app.post("/mcp")
async def mcp(request: Request):
    msg = await request.json()
    method = msg.get("method")
    id_ = msg.get("id")

    if id_ is None:  # notification
        return Response(status_code=202)

    if method == "initialize":
        pv = (msg.get("params") or {}).get("protocolVersion", "2025-03-26")
        return rpc_result(id_, {
            "protocolVersion": pv,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "exam-mcp", "version": "1.0.0"},
        })

    if method == "ping":
        return rpc_result(id_, {})

    if method == "tools/list":
        return rpc_result(id_, {"tools": [TOOL]})

    if method == "tools/call":
        if (msg.get("params") or {}).get("name") != "solve_challenge":
            return rpc_error(id_, -32602, "Unknown tool")
        challenge = request.headers.get("x-exam-challenge", "")
        text = hashlib.sha256(f"{challenge}:{EMAIL}".encode()).hexdigest()[:16]
        return rpc_result(id_, {"content": [{"type": "text", "text": text}]})

    return rpc_error(id_, -32601, "Method not found")