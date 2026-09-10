#!/usr/bin/env python3
"""Derive the CodeQL scan-language matrix strictly from the packs: keys of
codeql-config.yml, mapped through gate/config.json's languageMap.

Emits `matrix=<json>` to $GITHUB_OUTPUT (or stdout when run locally). Fails if a
packs key has no languageMap entry or no per-language floor block, so a new pack
language cannot be added without also gaining a test in the gate.

Stdlib only, and a deliberately small hand parser for the packs: block rather
than a YAML dependency (see the design's zero-dependency bias for this tooling).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def packs_keys(config_path):
    """Return the first-level keys under a top-level `packs:` mapping.

    The block ends at the next zero-indent line. Language keys are the lines at
    the first child-indent level that end in ":"; the pack list items beneath
    them start with "-" and are skipped.
    """
    keys = []
    in_packs = False
    child_indent = None
    with open(config_path) as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            if indent == 0:
                in_packs = line.strip() == "packs:"
                child_indent = None
                continue
            if not in_packs:
                continue
            if child_indent is None:
                child_indent = indent
            if indent == child_indent and line.strip().endswith(":"):
                keys.append(line.strip()[:-1])
    return keys


def main():
    config = json.load(open(os.path.join(HERE, "config.json")))
    lang_map = config["languageMap"]
    lang_cfg = config["languages"]

    keys = packs_keys(os.path.join(REPO, "codeql-config.yml"))
    if not keys:
        sys.exit("gate: no packs: keys found in codeql-config.yml")

    include = []
    errors = []
    for key in keys:
        scan_lang = lang_map.get(key)
        if scan_lang is None:
            errors.append(f"packs key '{key}' has no languageMap entry in gate/config.json")
            continue
        if scan_lang not in lang_cfg:
            errors.append(
                f"packs key '{key}' -> '{scan_lang}' has no floor/fixtures block in "
                f"gate/config.json (a new language needs a test before it can ship)"
            )
            continue
        include.append({"language": scan_lang, "build-mode": "none"})

    if errors:
        sys.exit("gate: " + "; ".join(errors))

    matrix = {"include": include}
    payload = json.dumps(matrix, separators=(",", ":"))
    print(f"Derived matrix from packs keys {keys}: {payload}", file=sys.stderr)

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"matrix={payload}\n")
    else:
        print(payload)


if __name__ == "__main__":
    main()
