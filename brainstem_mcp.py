#!/usr/bin/env python3
"""Connects Claude Code (or any MCP host) to a RAPP Brainstem running on this machine.

Tools:
    chat(user_input, session_id?)   talk to the brainstem; it picks its own agents
    capabilities()                  what the brainstem can do right now (/health)

Setup: https://kody-w.github.io/rapp-brainstem-claude/
Environment: BRAINSTEM_URL (default http://localhost:7071)
"""
from __future__ import annotations

import json
import os
import uuid

import requests
from mcp.server.mcpserver import MCPServer

BRAINSTEM_URL = (os.getenv("BRAINSTEM_URL") or "http://localhost:7071").rstrip("/")
CHAT_TIMEOUT = float(os.getenv("BRAINSTEM_MCP_TIMEOUT", "240"))
HISTORY_TURNS = 20

mcp = MCPServer("rapp-brainstem", version="1.0.0",
                instructions="A local RAPP Brainstem. Call `chat` with plain language; it chooses its own "
                             "agents. Pass the same `session_id` to continue a conversation.")

_history: dict[str, list[dict]] = {}


@mcp.tool()
def chat(user_input: str, session_id: str | None = None) -> str:
    """Send one message to the brainstem and get its answer.

    user_input: what you want, in plain language. The brainstem picks the agent that fits.
    session_id: pass the id from an earlier result to continue that conversation; omit to start fresh.
    Result JSON: response, session_id, model, agent_logs.
    """
    session_id = session_id or f"claude-{uuid.uuid4().hex[:12]}"
    history = _history.setdefault(session_id, [])
    body = {"user_input": user_input, "session_id": session_id,
            "conversation_history": history[-HISTORY_TURNS * 2:]}
    try:
        r = requests.post(f"{BRAINSTEM_URL}/chat", json=body, timeout=CHAT_TIMEOUT)
        data = r.json()
    except requests.RequestException as e:
        return json.dumps({"error": f"brainstem not reachable at {BRAINSTEM_URL} ({e}). "
                                    "Start it with: brainstem", "session_id": session_id})
    except ValueError:
        return json.dumps({"error": r.text[:500], "http_status": r.status_code, "session_id": session_id})
    if r.ok and data.get("response"):
        history += [{"role": "user", "content": user_input},
                    {"role": "assistant", "content": data["response"]}]
    data.setdefault("session_id", session_id)
    return json.dumps(data, ensure_ascii=False)


@mcp.tool()
def capabilities() -> str:
    """What this brainstem can do right now: status, version, model, and loaded agents."""
    try:
        return json.dumps(requests.get(f"{BRAINSTEM_URL}/health", timeout=30).json(), ensure_ascii=False)
    except (requests.RequestException, ValueError) as e:
        return json.dumps({"error": f"brainstem not reachable at {BRAINSTEM_URL} ({e}). Start it with: brainstem"})


if __name__ == "__main__":
    mcp.run()
