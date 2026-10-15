import hashlib
import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Your registered exam email, normalized: trimmed + lowercased
EMAIL = "24f3003132@ds.study.iitm.ac.in".strip().lower()

app = FastAPI()


def rpc_result(id_, result):
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": id_,
        "result": result,
    })


def rpc_error(id_, code, message):
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": id_,
        "error": {
            "code": code,
            "message": message,
        },
    })


@app.post("/")
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    method = body.get("method")
    id_ = body.get("id")
    params = body.get("params") or {}

    # Notifications have no id. Return 202 Accepted with no body.
    if id_ is None:
        return Response(status_code=202)

    if method == "initialize":
        # Echo the client's protocol version when present.
        protocol_version = params.get("protocolVersion") or "2024-11-05"
        return rpc_result(id_, {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "exam-mcp-server",
                "version": "1.0.0",
            },
        })

    if method == "tools/list":
        return rpc_result(id_, {
            "tools": [
                {
                    "name": "solve_challenge",
                    "description": "Returns the required SHA-256 challenge response.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    },
                }
            ]
        })

    if method == "tools/call":
        if params.get("name") != "solve_challenge":
            return rpc_error(id_, -32601, "Unknown tool")

        # Read the challenge from the HTTP request headers, per call.
        challenge = request.headers.get("x-exam-challenge")
        if not challenge:
            return rpc_error(id_, -32602, "Missing X-Exam-Challenge header")

        # Optional signature verification. Leave disabled unless you know the secret.
        # secret = os.environ.get("EXAM_SECRET")
        # if secret:
        #     timestamp = request.headers.get("x-exam-timestamp", "")
        #     signature = request.headers.get("x-exam-signature", "")
        #     msg = f"{challenge}.{timestamp}.{EMAIL}"
        #     expected = hmac.new(
        #         secret.encode(), msg.encode(), hashlib.sha256
        #     ).hexdigest()
        #     if not hmac.compare_digest(expected, signature):
        #         return rpc_error(id_, -32000, "Invalid signature")

        text = hashlib.sha256(
            f"{challenge}:{EMAIL}".encode("utf-8")
        ).hexdigest()[:16]

        return rpc_result(id_, {
            "content": [
                {
                    "type": "text",
                    "text": text,
                }
            ],
            "isError": False,
        })

    if method == "ping":
        return rpc_result(id_, {})

    return rpc_error(id_, -32601, f"Method not found: {method}")


@app.get("/")
async def health():
    return {"ok": True}


@app.get("/mcp")
async def mcp_get():
    # Streamable HTTP clients may probe GET; 405 is acceptable if you do not
    # provide a server-initiated SSE stream.
    return Response(status_code=405)


@app.options("/")
@app.options("/mcp")
async def mcp_options():
    return Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": (
            "Content-Type, Accept, Mcp-Session-Id, "
            "X-Exam-Challenge, X-Exam-Timestamp, X-Exam-Signature"
        ),
    })