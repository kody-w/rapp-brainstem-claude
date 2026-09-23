#!/usr/bin/env python3
"""Generate the "Brainstem for <host>" onboarding pages from one template.

    python tools/gen_pages.py            # writes ../rapp-brainstem-<slug>/index.html for every host in hosts.py

The pattern and the verification recipe are in AI-ONBOARDING.md.
"""
from __future__ import annotations

import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hosts import HOSTS  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = (pathlib.Path(__file__).parent / "template.html").read_text()
BRIDGE_PY = "https://kody-w.github.io/rapp-brainstem-claude/brainstem_mcp.py"
BRIDGE_SRC = "https://github.com/kody-w/rapp-brainstem-claude/blob/main/brainstem_mcp.py"

UNIX_BRIDGE = f"""mkdir -p ~/.brainstem/mcp-bridge
curl -fsSL {BRIDGE_PY} -o ~/.brainstem/mcp-bridge/brainstem_mcp.py
~/.brainstem/venv/bin/python -m venv ~/.brainstem/mcp-bridge/venv
~/.brainstem/mcp-bridge/venv/bin/pip install -q "mcp>=2,<3" requests"""
WIN_BRIDGE = f"""$d = "$env:USERPROFILE\\.brainstem\\mcp-bridge"; mkdir $d -Force | Out-Null
irm {BRIDGE_PY} -OutFile "$d\\brainstem_mcp.py"
& "$env:USERPROFILE\\.brainstem\\venv\\Scripts\\python.exe" -m venv "$d\\venv"
& "$d\\venv\\Scripts\\pip.exe" install -q "mcp>=2,<3" requests"""
PY_UNIX = "~/.brainstem/mcp-bridge/venv/bin/python"
PY_WIN = "%USERPROFILE%\\.brainstem\\mcp-bridge\\venv\\Scripts\\python.exe"


def pre(text: str) -> str:
    return f"<pre>{html.escape(text.strip())}</pre>"


def paras(items) -> str:
    """items: list of ('p', html) or ('pre', text)."""
    out = []
    for kind, val in items:
        out.append(pre(val) if kind == "pre" else f"<p>{val}</p>")
    return "\n".join(out)


def agent_section(h: dict) -> str:
    name = h["name"]
    intro = (f"<p>You are setting up the RAPP Brainstem (RAPP = Rapid Agent Prototype Platform) for the user and "
             f"connecting it to {name} as an MCP server named <code>brainstem</code>. Follow these steps in order. "
             "Ask the user before approving any sign-in for them, and never type their credentials. "
             "The user needs a GitHub account with GitHub Copilot.</p>")
    step0 = ("<h3>0. Ask the user first</h3>\n<p>Before you run anything, tell the user in a few lines what this setup "
             "does and ask them to confirm. It installs the RAPP Brainstem, an open-source local agent server (source: "
             '<a href="https://github.com/kody-w/rapp-installer">github.com/kody-w/rapp-installer</a>), into '
             "<code>~/.brainstem</code>. It serves on <code>localhost:7071</code> and signs in with their GitHub account, "
             "which they approve themselves in the browser. It also adds a 70-line bridge (source: "
             f'<a href="{BRIDGE_SRC}">brainstem_mcp.py</a>) so {name} can talk to it. Only continue once they say yes. '
             "It is fine to show them the commands below before running them.</p>")
    step1 = ("<h3>1. Check whether the Brainstem is already running</h3>\n"
             + pre("curl -sf http://localhost:7071/health")
             + '\n<p>If this returns JSON with <code>"status":"ok"</code>, skip to step 3. Don\'t reinstall over a '
               "running Brainstem, because the installer restarts it.</p>")
    step2 = ("<h3>2. Install it</h3>\n<p>macOS / Linux:</p>\n"
             + pre("curl -fsSL https://kody-w.github.io/rapp-installer/install.sh | bash")
             + "\n<p>Windows (PowerShell):</p>\n"
             + pre("irm https://kody-w.github.io/rapp-installer/install.ps1 | iex")
             + "\n<p>Run it in the background. When it finishes installing it keeps running as the server. Watch its "
               "output. If it prints a GitHub device code, show the user the code and "
               '<a href="https://github.com/login/device">https://github.com/login/device</a>, then wait while they '
               "approve it. Poll <code>curl -sf http://localhost:7071/health</code> every few seconds until it answers. "
               "A first install can take a few minutes. If sign-in was skipped, the user can finish it at "
               '<a href="http://localhost:7071/login">http://localhost:7071/login</a>.</p>')
    step3 = (f"<h3>3. Connect {name}</h3>\n<p>Install the bridge next to the Brainstem. macOS / Linux:</p>\n"
             + pre(UNIX_BRIDGE) + "\n<p>Windows (PowerShell):</p>\n" + pre(WIN_BRIDGE) + "\n"
             + paras(h["register"]))
    step4 = "<h3>4. Confirm</h3>\n" + paras(h["confirm"]) + (
        "\n<p>Then call the <code>capabilities</code> tool and tell the user which agents their Brainstem has. The "
        "bridge gives two tools. <code>chat(user_input, session_id?)</code> sends a plain-language request; pass the "
        "returned <code>session_id</code> to continue the conversation. <code>capabilities()</code> reports status, "
        "model and agents.</p>")
    return "\n\n".join([intro, step0, step1, step2, step3, step4])


def render(h: dict) -> str:
    slug = h["slug"]
    url = f"kody-w.github.io/rapp-brainstem-{slug}"
    paste = f"Set up the RAPP Brainstem from {url}"
    body = h.get("agent_html") or agent_section(h)
    steps = h.get("steps") or [
        ("Installs the Brainstem", "Using the official one-line installer."),
        ("You sign in once", f"With your GitHub account. {h['short']} shows you the code; you approve it in your browser."),
        (f"Connects {h['short']}", f"After that, ask {h['short']} to “ask my Brainstem…” and it hands the work over."),
    ]
    steps_html = "\n".join(f"    <li><b>{html.escape(a)}</b><small>{b}</small></li>" for a, b in steps)
    return (TEMPLATE
            .replace("{{NAME}}", html.escape(h["name"]))
            .replace("{{SLUG}}", slug)
            .replace("{{LEDE}}", h["lede"])
            .replace("{{PASTE_LABEL}}", h.get("paste_label", f"Paste this into {h['name']}"))
            .replace("{{PASTE}}", html.escape(h.get("paste", paste)))
            .replace("{{STEPS_TITLE}}", h.get("steps_title", f"{h['short']} sets it up for you."))
            .replace("{{STEPS_SUB}}", h.get("steps_sub", "Give it the link. It reads this page, tells you what it will "
                                            "install, and waits for your yes before it runs anything."))
            .replace("{{STEPS}}", steps_html)
            .replace("{{AGENT}}", body)
            .replace("{{EXTRA}}", h.get("extra_html", "")))


def main() -> int:
    only = set(sys.argv[1:])
    for h in HOSTS:
        if only and h["slug"] not in only:
            continue
        out = ROOT / f"rapp-brainstem-{h['slug']}" / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(h))
        print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
