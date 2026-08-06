from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .bridge import Bridge
from .config import load_config
from .errors import ConfigurationError
from .policy import Policy
from .redaction import contains_secret, redact_text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safe-mcp-bridge-v2")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run the newline-delimited stdio bridge")
    run.add_argument("config")
    doctor = sub.add_parser("doctor", help="Validate configuration without exposing credentials")
    doctor.add_argument("config")
    check = sub.add_parser("policy-check", help="Evaluate a method/tool against local policy")
    check.add_argument("config")
    check.add_argument("method")
    check.add_argument("--tool")
    scan = sub.add_parser("leak-scan", help="Scan a file for secret-shaped material")
    scan.add_argument("path")
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.command == "run":
            _run(args.config)
        elif args.command == "doctor":
            config = load_config(args.config)
            config.auth.header_value()
            print(json.dumps({"ok": True, "protocol": config.protocol.version}))
        elif args.command == "policy-check":
            config = load_config(args.config)
            params: dict[str, Any] = {}
            if args.tool:
                params["name"] = args.tool
            decision = Policy(config.policy).evaluate({"method": args.method, "params": params})
            print(json.dumps({"allowed": decision.allowed, "reason": decision.reason}))
            raise SystemExit(0 if decision.allowed else 2)
        elif args.command == "leak-scan":
            text = Path(args.path).read_text(encoding="utf-8")
            leaked = contains_secret(text)
            print(json.dumps({"clean": not leaked, "preview": redact_text(text)[:200]}))
            raise SystemExit(3 if leaked else 0)
    except (ConfigurationError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1) from exc


def _run(config_path: str) -> None:
    bridge = Bridge(load_config(config_path))
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("request must be a JSON object")
            responses = bridge.handle(request)
        except (json.JSONDecodeError, ValueError) as exc:
            responses = iter(
                [{"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}]
            )
        for response in responses:
            print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()

