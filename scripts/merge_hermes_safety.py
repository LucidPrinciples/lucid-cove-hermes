#!/usr/bin/env python3
"""Merge Lucid Cove house safety defaults into Hermes config.yaml without wiping the rest."""
from __future__ import annotations
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

cfg_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config.yaml")
if cfg_path.is_file():
    data = yaml.safe_load(cfg_path.read_text()) or {}
else:
    data = {}

# backups handled by caller
approvals = data.setdefault("approvals", {})
approvals["mode"] = "manual"
approvals["timeout"] = 300
approvals["cron_mode"] = "deny"
approvals["unattended_mode"] = "deny"
approvals["single_query_mode"] = "deny"
approvals["destructive_slash_confirm"] = True
deny = list(approvals.get("deny") or [])
for pat in ("git push --force*", "git push -f*"):
    if pat not in deny:
        deny.append(pat)
approvals["deny"] = deny

agent = data.setdefault("agent", {})
agent["max_turns"] = min(int(agent.get("max_turns") or 90), 60)

sr = data.setdefault("session_reset", {})
if "mode" not in sr:
    sr["mode"] = "none"

comp = data.setdefault("compression", {})
if "enabled" not in comp:
    comp["enabled"] = True

text = yaml.safe_dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
cfg_path.write_text(text)
print(f"updated {cfg_path}")
print("--- approvals ---")
print(yaml.safe_dump({"approvals": data["approvals"], "agent": {"max_turns": data["agent"]["max_turns"]}, "session_reset": data.get("session_reset")}, sort_keys=False))
