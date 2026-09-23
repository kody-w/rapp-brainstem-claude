"""One entry per AI host. gen_pages.py renders each into ../rapp-brainstem-<slug>/index.html.

`register` / `confirm` are lists of ('p', html) or ('pre', text). Sources for each host's syntax are
cited in AI-ONBOARDING.md; a host is only "verified" once its page passed the recipe there.
"""
import json

PY_U = "~/.brainstem/mcp-bridge/venv/bin/python"
SC_U = "~/.brainstem/mcp-bridge/brainstem_mcp.py"
PY_W = r'"$d\venv\Scripts\python.exe"'
SC_W = r'"$d\brainstem_mcp.py"'
ABS_U = "/Users/you/.brainstem/mcp-bridge/venv/bin/python"
ABS_S = "/Users/you/.brainstem/mcp-bridge/brainstem_mcp.py"
WIN_NOTE = (r"On Windows the command is <code>C:\\Users\\you\\.brainstem\\mcp-bridge\\venv\\Scripts\\python.exe</code> "
            r"and the argument is <code>C:\\Users\\you\\.brainstem\\mcp-bridge\\brainstem_mcp.py</code> "
            "(backslashes doubled inside JSON).")
ABS_NOTE = ("Use the user's real absolute paths (run <code>echo $HOME</code>; on Windows "
            "<code>$env:USERPROFILE</code>) in place of <code>/Users/you</code>. Config files do not expand <code>~</code>.")
MERGE = ("<b>Merge</b> this into the file, keeping every server already there. Create the file if it doesn't exist. "
         "If a <code>brainstem</code> entry already exists, ask the user before replacing it.")


def js(obj) -> str:
    return json.dumps(obj, indent=2)


def std_entry(**extra):
    return {"command": ABS_U, "args": [ABS_S], **extra}


def file_host(where: str, snippet: str, lang_note: str = "") -> list:
    return [("p", f"Then register it in {where}. {MERGE}"), ("pre", snippet),
            ("p", f"{ABS_NOTE} {WIN_NOTE} {lang_note}".strip())]


def cli_host(unix: str, win: str, note: str = "") -> list:
    out = [("p", "Then register it. macOS / Linux:"), ("pre", unix), ("p", "Windows (PowerShell, same <code>$d</code> as above):"), ("pre", win)]
    if note:
        out.append(("p", note))
    return out


def lede(short, where="without leaving it"):
    return (f"Your own AI agent server, running on your computer. {short} installs it and connects to it, "
            f"so you can hand work to your agents {where}.")


HOSTS = [
    {
        "slug": "codex", "name": "Codex CLI", "short": "Codex", "lede": lede("Codex CLI", "without leaving the terminal"),
        "register": cli_host(
            f"codex mcp add brainstem -- {PY_U} {SC_U}",
            f"codex mcp add brainstem -- {PY_W} {SC_W}",
            "Brainstem answers can take a while. In <code>~/.codex/config.toml</code>, add "
            "<code>tool_timeout_sec = 300</code> under the <code>[mcp_servers.brainstem]</code> table the command created. "
            "If <code>codex mcp list</code> already shows <code>brainstem</code>, ask the user before replacing it."),
        "confirm": [("pre", "codex mcp list"), ("p", "It should list <code>brainstem</code>. Codex loads MCP servers at startup, so tell the user to restart Codex.")],
    },
    {
        "slug": "vscode", "name": "VS Code", "short": "Copilot in VS Code",
        "lede": lede("GitHub Copilot in VS Code", "without leaving your editor"),
        "paste_label": "Paste this into Copilot Chat (Agent mode) in VS Code",
        "steps_title": "Copilot sets it up for you.",
        "register": cli_host(
            'code --add-mcp "{\\"name\\":\\"brainstem\\",\\"command\\":\\"$HOME/.brainstem/mcp-bridge/venv/bin/python\\",\\"args\\":[\\"$HOME/.brainstem/mcp-bridge/brainstem_mcp.py\\"]}"',
            "code --add-mcp (@{name='brainstem'; command=\"$d\\venv\\Scripts\\python.exe\"; args=@(\"$d\\brainstem_mcp.py\")} | ConvertTo-Json -Compress)",
            "This writes the user-level <code>mcp.json</code>, whose top-level key is <code>servers</code>. "
            "If <code>brainstem</code> is already in that file (command <em>MCP: Open User Configuration</em>), ask the user before replacing it."),
        "confirm": [("p", "Ask the user to run <b>MCP: List Servers</b> from the Command Palette and start <code>brainstem</code> if it isn't running. "
                          "New chats in Agent mode then have its tools.")],
    },
    {
        "slug": "cursor", "name": "Cursor", "short": "Cursor", "lede": lede("Cursor", "without leaving your editor"),
        "paste_label": "Paste this into Cursor's Agent chat",
        "register": file_host("<code>~/.cursor/mcp.json</code> (Windows: <code>%USERPROFILE%\\.cursor\\mcp.json</code>)",
                              js({"mcpServers": {"brainstem": {"type": "stdio", **std_entry()}}})),
        "confirm": [("p", "Ask the user to open <b>Cursor Settings → MCP</b> (or Tools &amp; Integrations) and check <code>brainstem</code> shows as enabled with two tools. Reload the window if it doesn't appear.")],
    },
    {
        "slug": "gemini", "name": "Gemini CLI", "short": "Gemini", "lede": lede("Gemini CLI", "without leaving the terminal"),
        "register": cli_host(
            f"gemini mcp add -s user brainstem {PY_U} {SC_U}",
            f"gemini mcp add -s user brainstem {PY_W} {SC_W}",
            "<code>-s user</code> matters: the default scope is the current project only. "
            "If <code>gemini mcp list</code> already shows <code>brainstem</code>, ask the user before replacing it."),
        "confirm": [("pre", "gemini mcp list"), ("p", "It should show <code>brainstem</code> as connected. New Gemini sessions have its tools; <code>/mcp</code> lists them.")],
    },
    {
        "slug": "windsurf", "name": "Windsurf", "short": "Windsurf", "lede": lede("Windsurf", "without leaving your editor"),
        "paste_label": "Paste this into Windsurf's Cascade chat",
        "steps_title": "Cascade sets it up for you.",
        "register": file_host(
            "Windsurf's MCP config: <code>~/.codeium/windsurf/mcp_config.json</code>, or on newer builds "
            "<code>~/.config/devin/mcp_config.json</code> (Windows: <code>%APPDATA%\\devin\\mcp_config.json</code>). "
            "Use whichever exists; if neither, ask the user to open Cascade → <b>MCPs</b> → Configure, which creates it",
            js({"mcpServers": {"brainstem": std_entry()}})),
        "confirm": [("p", "Ask the user to open Cascade → <b>MCPs</b> and press refresh. <code>brainstem</code> should show two tools.")],
    },
    {
        "slug": "cline", "name": "Cline", "short": "Cline", "lede": lede("Cline", "without leaving your editor"),
        "register": file_host(
            "Cline's MCP settings. For the Cline CLI that's <code>~/.cline/data/settings/cline_mcp_settings.json</code>. "
            "For the VS Code extension, ask the user to click <b>MCP Servers → Configure MCP Servers</b>, which opens the file "
            "(<code>…/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json</code>)",
            js({"mcpServers": {"brainstem": std_entry(timeout=300, disabled=False)}}),
            "<code>timeout</code> is in seconds."),
        "confirm": [("p", "The MCP Servers panel should show <code>brainstem</code> with a green dot and two tools. Cline reloads the file on save.")],
    },
    {
        "slug": "goose", "name": "Goose", "short": "Goose", "lede": lede("Goose", "without leaving it"),
        "register": [("p", "Then register it in <code>~/.config/goose/config.yaml</code> (Windows: <code>%APPDATA%\\Block\\goose\\config\\config.yaml</code>). "
                           + MERGE.replace("server", "extension") + " Add this under the existing <code>extensions:</code> key:"),
                     ("pre", "  brainstem:\n    name: brainstem\n    type: stdio\n    cmd: " + ABS_U + "\n    args: [\"" + ABS_S + "\"]\n"
                             "    enabled: true\n    bundled: false\n    env_keys: []\n    envs: {}\n    timeout: 300"),
                     ("p", ABS_NOTE + " <code>timeout</code> is in seconds.")],
        "confirm": [("p", "Goose loads extensions when a session starts. Tell the user to start a new session and check <code>brainstem</code> is listed (<code>goose configure</code> → Toggle Extensions).")],
    },
    {
        "slug": "opencode", "name": "OpenCode", "short": "OpenCode", "lede": lede("OpenCode", "without leaving the terminal"),
        "register": file_host("<code>~/.config/opencode/opencode.json</code>",
                              js({"$schema": "https://opencode.ai/config.json",
                                  "mcp": {"brainstem": {"type": "local", "command": [ABS_U, ABS_S], "enabled": True, "timeout": 300000}}}),
                              "OpenCode's key is <code>mcp</code>, the type is <code>local</code>, and <code>command</code> is one array holding both paths. <code>timeout</code> is in milliseconds."),
        "confirm": [("pre", "opencode mcp list"), ("p", "It should list <code>brainstem</code> as connected. Restart OpenCode to load it.")],
    },
    {
        "slug": "kiro", "name": "Kiro", "short": "Kiro", "lede": lede("Kiro", "without leaving your editor"),
        "register": file_host("<code>~/.kiro/settings/mcp.json</code> (Windows: <code>%USERPROFILE%\\.kiro\\settings\\mcp.json</code>)",
                              js({"mcpServers": {"brainstem": std_entry(disabled=False, autoApprove=[])}})),
        "confirm": [("p", "Kiro reloads MCP config on save. Ask the user to check the <b>MCP servers</b> tab in the Kiro panel shows <code>brainstem</code> connected.")],
    },
]

# ---------------------------------------------------------------- Claude Desktop: one-click extension
_DESKTOP_AGENT = """<p>Claude Desktop can't run an installer itself, so this page is for the person. If you are an AI agent that <em>can</em> run shell commands, help them like this, asking before each step:</p>
<h3>1. Install the Brainstem</h3>
<pre>curl -fsSL https://kody-w.github.io/rapp-installer/install.sh | bash</pre>
<p>Windows (PowerShell): <code>irm https://kody-w.github.io/rapp-installer/install.ps1 | iex</code>. Skip this if <code>curl -sf http://localhost:7071/health</code> already answers.</p>
<h3>2. Install the extension</h3>
<p>Download <a href="brainstem.mcpb">brainstem.mcpb</a> and open it (<code>open brainstem.mcpb</code> on macOS). Claude Desktop shows an install dialog; the user clicks <b>Install</b>. It needs no Python: it runs on the Node.js built into Claude Desktop. Source: <a href="https://github.com/kody-w/rapp-brainstem-claude-desktop">github.com/kody-w/rapp-brainstem-claude-desktop</a>.</p>
<h3>3. Confirm</h3>
<p>In Claude Desktop, <b>Settings → Extensions</b> shows <b>RAPP Brainstem</b> enabled. Ask Claude: “Ask my Brainstem what it can do.”</p>"""

HOSTS.append({
    "slug": "claude-desktop", "name": "Claude Desktop", "short": "Claude",
    "lede": "Your own AI agent server, running on your computer, connected to Claude Desktop with a one-click extension.",
    "paste_label": "1. Paste this into Terminal (Mac) to install the Brainstem",
    "paste": "curl -fsSL https://kody-w.github.io/rapp-installer/install.sh | bash",
    "extra_html": ('<p class="note">On Windows, paste into PowerShell: <code>irm https://kody-w.github.io/rapp-installer/install.ps1 | iex</code></p>\n'
                   '  <p class="paste-label">2. Add it to Claude Desktop</p>\n'
                   '  <a class="dl" href="brainstem.mcpb" download>Download the Brainstem extension</a>\n'
                   '  <p class="note">Double-click the downloaded file. Claude Desktop opens it; click <b>Install</b>.</p>'),
    "steps_title": "Two steps, then just ask.",
    "steps_sub": "The installer sets up the Brainstem and signs you in with GitHub. The extension connects Claude to it.",
    "steps": [("Install the Brainstem", "Paste the line above into Terminal. Approve the GitHub sign-in when it asks."),
              ("Add the extension", "Download it, double-click, click Install. No Python or settings to edit."),
              ("Ask Claude", "Try “Ask my Brainstem what it can do.”")],
    "agent_html": _DESKTOP_AGENT,
})

# ---------------------------------------------------------------- Any MCP host
_GENERIC_CONFIG = js({"mcpServers": {"brainstem": std_entry()}})
HOSTS.append({
    "slug": "mcp", "name": "any MCP app", "short": "Your AI",
    "lede": "Your own AI agent server, running on your computer, connected to any AI app that supports MCP.",
    "paste_label": "Paste this into any AI agent that can run commands",
    "steps_title": "Works with any MCP app.",
    "steps_sub": "Agents that can run commands set it up from the link. For apps that can't, use the settings below.",
    "steps": [("Installs the Brainstem", "Using the official one-line installer."),
              ("Adds a small bridge", "One file, the same for every app."),
              ("Registers it", "In your app's MCP settings, under the name <b>brainstem</b>.")],
    "register": [("p", "Then register it with the user's AI app as a <b>local (stdio) MCP server</b> named <code>brainstem</code>. "
                       "If the app has a command for this (for example <code>&lt;app&gt; mcp add brainstem -- &lt;command&gt; &lt;arg&gt;</code>), use it. "
                       "Otherwise merge it into the app's MCP config file, keeping every server already there; if a <code>brainstem</code> entry exists, ask the user before replacing it. Most apps use this shape:"),
                 ("pre", _GENERIC_CONFIG),
                 ("p", ABS_NOTE + " " + WIN_NOTE + " Some apps name the top-level key <code>servers</code> or <code>mcp</code>; follow the app's own docs for the key and file location. "
                       "If the app has Node.js 18+ and no Python, a zero-dependency Node version of the same bridge works too: "
                       "<code>node brainstem_mcp.js</code> (<a href=\"https://kody-w.github.io/rapp-brainstem-claude/brainstem_mcp.js\">brainstem_mcp.js</a>)."),
                 ("p", "Per-app pages with exact steps: "
                       + ", ".join(f'<a href="https://kody-w.github.io/rapp-brainstem-{s}/">{n}</a>' for s, n in (
                           ("claude", "Claude Code"), ("copilot", "Copilot CLI"), ("codex", "Codex"), ("vscode", "VS Code"),
                           ("cursor", "Cursor"), ("gemini", "Gemini CLI"), ("claude-desktop", "Claude Desktop"), ("windsurf", "Windsurf"),
                           ("cline", "Cline"), ("goose", "Goose"), ("opencode", "OpenCode"), ("kiro", "Kiro"))) + ".")],
    "confirm": [("p", "Restart the app or reload its MCP servers, and check <code>brainstem</code> is listed with two tools.")],
})
