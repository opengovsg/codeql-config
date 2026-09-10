#!/usr/bin/env python3
"""Assert a CodeQL SARIF from THIS run meets the deployment-gate floors.

Usage: assert.py <scan-language> <sarif-file>

Reads gate/config.json for the language's floor, expected custom rule ids, and
known-bad / known-good fixture expectations, then checks them against the SARIF
produced by the scan of this commit (no upload, no baseline filtering — findings
are read straight from the run's own output). Exits non-zero on any failure.

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


def results(sarif):
    """Yield (rule_id, [location-uris]) for every result in the SARIF."""
    for run in sarif.get("runs", []):
        rules = run.get("tool", {}).get("driver", {}).get("rules", []) or []
        for res in run.get("results", []) or []:
            rid = res.get("ruleId")
            if rid is None and "ruleIndex" in res and res["ruleIndex"] < len(rules):
                rid = rules[res["ruleIndex"]].get("id")
            if rid is None:
                rid = res.get("rule", {}).get("id")
            uris = []
            for loc in res.get("locations", []) or []:
                uri = (
                    loc.get("physicalLocation", {})
                    .get("artifactLocation", {})
                    .get("uri")
                )
                if uri:
                    uris.append(uri)
            yield rid, uris


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
    all_results = list(results(sarif))

    checks = []  # (ok, message)

    # (a) query-count floor
    floor = lang["queryCountFloor"]
    checks.append(
        (len(rule_ids) >= floor, f"query-count {len(rule_ids)} >= floor {floor}")
    )

    # (b) expected custom rule ids present in the loaded set
    for rid in lang.get("expectedRuleIds", []):
        checks.append((rid in rule_ids, f"expected rule id loaded: {rid}"))

    # (c) known-bad fixture produces >=1 finding for its named rule
    bad = lang["badFixture"]
    bad_hits = [
        u
        for rid, uris in all_results
        if rid == bad["ruleId"]
        for u in uris
        if bad["pathContains"] in u
    ]
    checks.append(
        (
            len(bad_hits) >= 1,
            f"known-bad fixture fires {bad['ruleId']} "
            f"({len(bad_hits)} finding(s) under {bad['pathContains']})",
        )
    )

    # (c) known-good fixture stays completely silent
    good = lang["goodFixture"]
    good_hits = [
        (rid, u)
        for rid, uris in all_results
        for u in uris
        if good["pathContains"] in u
    ]
    checks.append(
        (
            len(good_hits) == 0,
            f"known-good fixture silent (0 findings under {good['pathContains']}"
            + (f"; got {good_hits}" if good_hits else "")
            + ")",
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
