#!/usr/bin/env python3
"""Regenerate the README API reference section (between the GENERATED
markers) from the OpenAPI spec, so the published method tables can never
drift from the live contract. Run manually or from the generate workflow.

Stdlib only. Method names mirror openapi-generator's camelCase -> snake_case
conversion so they match the generated API classes exactly.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

DEFAULT_SPEC_URL = "https://api.onepostly.com/openapi.json"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
BEGIN = "<!-- BEGIN GENERATED API REFERENCE -->"
END = "<!-- END GENERATED API REFERENCE -->"


def to_snake(name: str) -> str:
    # Same multi-step conversion openapi-generator's python generator applies.
    step = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    step = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", step)
    return step.replace("-", "_").lower()


def load_spec(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    # The API gateway rejects requests without a User-Agent (403).
    request = urllib.request.Request(
        DEFAULT_SPEC_URL, headers={"User-Agent": "onepostly-sdk-scripts"}
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def collect_groups(spec: dict) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for methods in (spec.get("paths") or {}).values():
        for verb, op in methods.items():
            if verb not in HTTP_METHODS:
                continue
            tags = op.get("tags") or []
            if not tags or not op.get("operationId"):
                continue
            summary = (op.get("summary") or "").replace("|", "\\|").strip()
            groups.setdefault(tags[0], []).append(
                {"id": op["operationId"], "snake": to_snake(op["operationId"]), "summary": summary}
            )
    return groups


def api_reference(spec: dict) -> str:
    groups = collect_groups(spec)
    declared = [t["name"] for t in spec.get("tags") or [] if t["name"] in groups]
    rest = sorted(t for t in groups if t not in declared)
    lines: list[str] = []
    for tag in declared + rest:
        instance = tag[:1].lower() + tag[1:]
        lines += [f"### {tag}Api", "", "| Method | Description |", "| --- | --- |"]
        for op in groups[tag]:
            lines.append(f"| `{instance}.{op['snake']}()` | {op['summary']} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate the README API reference section.")
    parser.add_argument("--spec", help="Path to a local OpenAPI spec (default: fetch live spec)")
    parser.add_argument("--readme", default="README.md")
    args = parser.parse_args()

    readme = Path(args.readme)
    content = readme.read_text(encoding="utf-8")
    begin = content.find(BEGIN)
    end = content.find(END)
    if begin == -1 or end == -1 or end < begin:
        raise SystemExit(f"README is missing the {BEGIN} / {END} markers.")

    updated = (
        content[: begin + len(BEGIN)] + "\n\n" + api_reference(load_spec(args.spec)) + "\n" + content[end:]
    )
    readme.write_text(updated, encoding="utf-8")
    print(f"API reference regenerated in {args.readme}.")


if __name__ == "__main__":
    main()
