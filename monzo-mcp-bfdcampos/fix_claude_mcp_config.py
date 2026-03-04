#!/usr/bin/env python3
"""
Fix the Monzo MCP entry in Claude Desktop config after `mcp install`.
mcp install writes only --with mcp[cli], which causes "Server disconnected"
(ModuleNotFoundError: requests). This script adds requests, python-dotenv,
and --env-file to the Monzo server args.
"""
import json
import os
import sys
from pathlib import Path

# Claude Desktop config path (macOS)
CLAUDE_CONFIG_PATH = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"


def main() -> None:
    if not CLAUDE_CONFIG_PATH.exists():
        print(f"Claude config not found: {CLAUDE_CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(CLAUDE_CONFIG_PATH, "r") as f:
        config = json.load(f)

    servers = config.get("mcpServers") or {}
    if "Monzo" not in servers:
        print("Monzo server not found in config. Run: uv run mcp install main.py", file=sys.stderr)
        sys.exit(1)

    args = servers["Monzo"].get("args")
    if not isinstance(args, list):
        print("Monzo args is not a list; cannot patch.", file=sys.stderr)
        sys.exit(1)

    # Find --with and the next element (package list)
    try:
        i_with = args.index("--with")
    except ValueError:
        print("--with not found in Monzo args.", file=sys.stderr)
        sys.exit(1)

    # Ensure we have requests and python-dotenv
    pkg = args[i_with + 1]
    if "requests" not in pkg:
        pkg = pkg.rstrip(",") + ",requests,python-dotenv" if pkg else "mcp[cli],requests,python-dotenv"
        args[i_with + 1] = pkg

    # Find path to main.py (last element or the one after "run")
    main_path = None
    for i, a in enumerate(args):
        if isinstance(a, str) and a.endswith("main.py"):
            main_path = Path(a).resolve()
            break
    if not main_path or not main_path.exists():
        print("Could not find main.py path in args.", file=sys.stderr)
        sys.exit(1)

    env_file = main_path.parent / ".env"

    # Insert --env-file and path after the package list (before "mcp")
    if "--env-file" not in args:
        insert_at = i_with + 2
        args[insert_at:insert_at] = ["--env-file", str(env_file)]

    with open(CLAUDE_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print("Updated Claude config: Monzo args now include requests, python-dotenv, and --env-file.")
    print("Restart Claude Desktop and try Monzo again.")


if __name__ == "__main__":
    main()
