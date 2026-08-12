"""Workflow-facing admission command; effects remain in explicit workflow phases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import requests

from .contract import COMPATIBILITY_SHA, ContractError, validate_request

RAW = f"https://raw.githubusercontent.com/Young-Consultations/.github/{COMPATIBILITY_SHA}/contracts"


def _json(source: str) -> dict:
    if source.startswith("https://"):
        response = requests.get(source, timeout=30)
        response.raise_for_status()
        value = response.json()
    else:
        value = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError("JSON document must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--schema", default=f"{RAW}/execution-input.schema.json")
    parser.add_argument("--concurrency-group", required=True)
    parser.add_argument("--caller-repository", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        request = validate_request(
            _json(args.input),
            schema=_json(args.schema),
            concurrency_group=args.concurrency_group,
            caller_repository=args.caller_repository,
        )
    except Exception as exc:
        print(f"target admission rejected: {str(exc)[:512]}", file=sys.stderr)
        return 2
    Path(args.output).write_text(
        json.dumps(
            {
                "delivery_id": request.delivery_id,
                "mode": request.mode,
                "payload_digest": request.payload_digest,
            }
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
