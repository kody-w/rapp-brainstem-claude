#!/usr/bin/env node
// Connects Claude Desktop (or any MCP host) to a RAPP Brainstem on this machine.
// Same two tools as brainstem_mcp.py: chat(user_input, session_id?) and capabilities().
// No dependencies: speaks MCP's newline-delimited JSON-RPC over stdio directly.
"use strict";
const readline = require("readline");
const crypto = require("crypto");

const BRAINSTEM_URL = (process.env.BRAINSTEM_URL || "http://localhost:7071").replace(/\/+$/, "");
const CHAT_TIMEOUT_MS = 240000;
const HISTORY_TURNS = 20;
const history = new Map();

const TOOLS = [
  {
    name: "chat",
    description: "Send one message to the brainstem and get its answer. It picks the agent that fits. " +
      "Pass the session_id from an earlier result to continue that conversation; omit to start fresh. " +
      "Result JSON: response, session_id, model, agent_logs.",
    inputSchema: {
      type: "object",
      properties: {
        user_input: { type: "string", description: "What you want, in plain language." },
        session_id: { type: "string", description: "Id from an earlier result, to continue that conversation." },
      },
      required: ["user_input"],
    },
  },
  {
    name: "capabilities",
    description: "What this brainstem can do right now: status, version, model, and loaded agents.",
    inputSchema: { type: "object", properties: {} },
  },
];

const unreachable = (e) => `brainstem not reachable at ${BRAINSTEM_URL} (${e.message || e}). Start it with: brainstem`;

async function chat({ user_input, session_id }) {
  session_id = session_id || `claude-${crypto.randomBytes(6).toString("hex")}`;
  const past = history.get(session_id) || [];
  const body = { user_input, session_id, conversation_history: past.slice(-HISTORY_TURNS * 2) };
  let r, data;
  try {
    r = await fetch(`${BRAINSTEM_URL}/chat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(CHAT_TIMEOUT_MS),
    });
  } catch (e) {
    return { error: unreachable(e), session_id };
  }
  const text = await r.text();
  try { data = JSON.parse(text); } catch { return { error: text.slice(0, 500), http_status: r.status, session_id }; }
  if (r.ok && data.response) {
    past.push({ role: "user", content: user_input }, { role: "assistant", content: data.response });
    history.set(session_id, past);
  }
  if (!data.session_id) data.session_id = session_id;
  return data;
}

async function capabilities() {
  try {
    const r = await fetch(`${BRAINSTEM_URL}/health`, { signal: AbortSignal.timeout(30000) });
    return await r.json();
  } catch (e) {
    return { error: unreachable(e) };
  }
}

const send = (msg) => process.stdout.write(JSON.stringify(msg) + "\n");

async function handle(msg) {
  const { id, method, params } = msg;
  if (id === undefined) return; // notifications need no reply
  const ok = (result) => send({ jsonrpc: "2.0", id, result });
  switch (method) {
    case "initialize":
      return ok({
        protocolVersion: (params && params.protocolVersion) || "2025-06-18",
        capabilities: { tools: {} },
        serverInfo: { name: "rapp-brainstem", version: "1.0.0" },
        instructions: "A local RAPP Brainstem. Call `chat` with plain language; it chooses its own agents. " +
          "Pass the same `session_id` to continue a conversation.",
      });
    case "ping":
      return ok({});
    case "tools/list":
      return ok({ tools: TOOLS });
    case "tools/call": {
      const name = params && params.name;
      const args = (params && params.arguments) || {};
      if (name !== "chat" && name !== "capabilities") {
        return send({ jsonrpc: "2.0", id, error: { code: -32602, message: `Unknown tool: ${name}` } });
      }
      const out = name === "chat" ? await chat(args) : await capabilities();
      return ok({ content: [{ type: "text", text: JSON.stringify(out) }], isError: Boolean(out.error) });
    }
    default:
      return send({ jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } });
  }
}

readline.createInterface({ input: process.stdin }).on("line", (line) => {
  if (!line.trim()) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return send({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } }); }
  handle(msg).catch((e) => msg.id !== undefined &&
    send({ jsonrpc: "2.0", id: msg.id, error: { code: -32603, message: String(e.message || e) } }));
});
