#!/usr/bin/env python3
"""Assert a CodeQL SARIF from THIS run meets the deployment-gate floors.

Usage: assert.py <scan-language> <sarif-file>

Reads gate/config.json for the language's query-count floor, expected custom
rule ids, and scanned-file floor, then checks them against the SARIF produced by
the scan of this commit (no upload, no baseline filtering — everything is read
straight from the run's own output). Exits non-zero on any failure.

The three checks map onto the silent failure modes this config can cause:
  - query count below floor      -> query-filters over-excluding
  - expected rule id missing     -> a pack that installs but skips its queries,
                                    or a CLI bump that dropped it
  - zero files scanned           -> paths-ignore swallowing the scan
Whether an individual query is any good is a question about the QUERY, tested by
codeql-pack's unit tests and fixtures — deliberately not duplicated here.

Stdlib only.
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


def scanned_files(sarif):
    """Files the scan actually covered, per the SARIF artifact inventory."""
    uris = set()
    for run in sarif.get("runs", []):
        for art in run.get("artifacts", []) or []:
            uri = art.get("location", {}).get("uri")
            if uri:
                uris.add(uri)
    return uris


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
    files = scanned_files(sarif)

    checks = []  # (ok, message)

    floor = lang["queryCountFloor"]
    checks.append(
        (len(rule_ids) >= floor, f"query-count {len(rule_ids)} >= floor {floor}")
    )

    for rid in lang.get("expectedRuleIds", []):
        checks.append((rid in rule_ids, f"expected rule id loaded: {rid}"))

    file_floor = lang["scannedFilesFloor"]
    checks.append(
        (
            len(files) >= file_floor,
            f"scanned-files {len(files)} >= floor {file_floor} "
            f"(guards against paths-ignore swallowing the scan)",
        )
    )

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
