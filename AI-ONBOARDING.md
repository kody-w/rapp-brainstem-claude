# AI onboarding pages — the pattern

One page per AI host. A person pastes a single line into that host, and the host installs the
RAPP Brainstem and connects to it. The model is Zernio's `zernio.com/claude`.

| Host | Page | Paste line |
| --- | --- | --- |
| Claude Code | https://kody-w.github.io/rapp-brainstem-claude/ | `Set up the RAPP Brainstem from kody-w.github.io/rapp-brainstem-claude` |
| GitHub Copilot CLI | https://kody-w.github.io/rapp-brainstem-copilot/ | `Set up the RAPP Brainstem from kody-w.github.io/rapp-brainstem-copilot` |

## Page anatomy (copy `index.html` from an existing page)

1. **Human half.** A title (`Brainstem for <Host>`), one plain sentence, the paste line inside a copy button, three chips and three steps: installs, you sign in once, connects. No commands here.
2. **Agent half.** A collapsed `<details>` section headed **"For AI agents reading this page"**, holding numbered steps:
   0. **Ask the user first.** Say what gets installed (with source links) and wait for a yes. This step is required, see below.
   1. `curl -sf http://localhost:7071/health`. If the Brainstem is already running, skip the install, because the installer restarts it.
   2. Install from the Pages URLs only: `https://kody-w.github.io/rapp-installer/install.sh` / `install.ps1`. Run it in the background. If a device code appears, relay it and wait for the user to approve.
   3. Install the shared bridge into `~/.brainstem/<dir>/venv`, built from `~/.brainstem/venv/bin/python`, which is 3.11 or newer so `mcp>=2` installs. Then register it with the host's own `mcp add` command.
   4. Confirm with the host's `mcp get`. Tell the user to restart, then call `capabilities`.
   Include "If a `brainstem` server already exists, ask before replacing it."

## The shared bridge

`brainstem_mcp.py` (this repo, about 70 lines) is the only bridge. Every page downloads it from
`https://kody-w.github.io/rapp-brainstem-claude/brainstem_mcp.py`. Don't copy it into other
repos. It exposes `chat(user_input, session_id?)`, which keeps per-session history and sends it as
`conversation_history`, and `capabilities()`, which returns `/health`. It works against the grail
brainstem's `/chat` contract (the answer is in the `response` field).

## Why step 0 is required

The first Copilot CLI test (2026-09-23), run without a consent step, **refused**. It read the page as
prompt injection: "a webpage crafted to get an AI agent to auto-install and auto-authorize unknown
third-party software". That was a reasonable call. The fix was consent and transparency: say what is
installed, link the source, and wait for a yes. Never reword a page to get past an agent's safety
judgment. After the fix, the same one-shot test completed the setup. In `-p` mode Copilot treated
the pasted line itself as the user's yes.

## Verification recipe (required before calling a page done)

Run it in a throwaway home so the real config is never touched:

```bash
T=$(gh auth token)      # compute BEFORE overriding HOME: zsh applies prefix assignments left to right
H=$SCRATCH/home; mkdir -p $H/.brainstem $H/work; ln -s ~/.brainstem/venv $H/.brainstem/venv
cd $H/work
# 1. the host sets itself up from the paste line alone
HOME=$H COPILOT_HOME=$H/.copilot GH_TOKEN=$T copilot -p "Set up the RAPP Brainstem from kody-w.github.io/<page>" --allow-all-tools --allow-all-urls
# 2. a NEW session actually uses the tool
HOME=$H COPILOT_HOME=$H/.copilot GH_TOKEN=$T copilot -p "Ask my Brainstem to reply with exactly: BRAINSTEM-OK. Use the brainstem MCP chat tool." --allow-all-tools
```

It passes only if step 2 shows the host calling `chat (MCP: brainstem)` and getting the reply back.
For Claude Code, `claude mcp get brainstem` must also show `Connected` in the isolated `HOME`.
Also take desktop (1280) and phone (390) screenshots of the live page.

## Shipping

New public repo `kody-w/rapp-brainstem-<host>`, containing `index.html`, `.nojekyll` and a
README. Enable Pages on `main` at `/`, and check that the live page serves the new content before
handing over the link. Never push to `kody-w/rapp-installer`.

## Backlog: next hosts (by reach × fit)

Each needs a shell tool (to run the installer) and MCP support. The exact `mcp add` syntax for each is **unverified** until its page passes the recipe.

1. **OpenAI Codex CLI**: `codex mcp add brainstem -- <python> <bridge>`
2. **VS Code (Copilot agent mode)**: `code --add-mcp '{"name":"brainstem","command":...}'`
3. **Cursor**: `~/.cursor/mcp.json` (or a cursor:// install deeplink)
4. **Gemini CLI**: `gemini mcp add brainstem <python> <bridge>`
5. **Claude Desktop**: has no shell, so it can't self-install. Ship a `.mcpb` desktop extension, and the page tells the user to install the Brainstem with the one-liner first.
6. **Windsurf**: `~/.codeium/windsurf/mcp_config.json`
7. **Cline**: `cline_mcp_settings.json` via the MCP Servers panel
8. **Goose**: `goose configure` → add extension (or goose:// deeplink)
9. **OpenCode**: `opencode.json` → `mcp` block
10. **Kiro**: `~/.kiro/settings/mcp.json`
