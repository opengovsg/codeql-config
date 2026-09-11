#!/usr/bin/env python3
"""Assert a scan's SARIF meets the floors in gate/config.json. See gate/README.md.

Usage: assert.py <scan-language> <sarif-file>

Reads the SARIF of this run directly, so nothing is baseline-filtered.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def loaded_rule_ids(sarif):
    """All rule ids advertised by the tool (driver + pack extensions)."""
    ids = set()
    for run in sarif.get("runs", []):
        tool = run.get("tool", {})
        for rule in tool.get("driver", {}).get("rules", []) or []:
            if rule.get("id"):
                ids.add(rule["id"])
        for ext in tool.get("extensions", []) or []:
            for rule in ext.get("rules", []) or []:
                if rule.get("id"):
                    ids.add(rule["id"])
    return ids


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: assert.py <scan-language> <sarif-file>")
    language, sarif_path = sys.argv[1], sys.argv[2]

    config = json.load(open(os.path.join(HERE, "config.json")))
    lang = config["languages"].get(language)
    if lang is None:
        sys.exit(f"gate: no config block for language '{language}'")

    sarif = json.load(open(sarif_path))
    rule_ids = loaded_rule_ids(sarif)

    checks = []  # (ok, message)

    floor = lang["queryCountFloor"]
    checks.append(
        (len(rule_ids) >= floor, f"query-count {len(rule_ids)} >= floor {floor}")
    )

    for rid in lang.get("expectedRuleIds", []):
        checks.append((rid in rule_ids, f"expected rule id loaded: {rid}"))

    passed = all(ok for ok, _ in checks)
    lines = [f"### Deployment gate: {language} — {'PASS' if passed else 'FAIL'}", ""]
    for ok, msg in checks:
        lines.append(f"- {'✅' if ok else '❌'} {msg}")
    report = "\n".join(lines)
    print(report)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write(report + "\n\n")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
