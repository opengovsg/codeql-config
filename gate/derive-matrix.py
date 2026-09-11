#!/usr/bin/env python3
"""Derive the scan-language matrix from codeql-config.yml's packs: keys.

Emits `matrix=<json>` to $GITHUB_OUTPUT (or stdout locally). Fails if a packs key
has no languageMap entry or floor block in gate/config.json, so a new language
cannot ship without a test. See gate/README.md.

Python, not Node: this must parse YAML, and PyYAML ships on the runner whereas
Node has no stdlib YAML and would need an npm dependency.
"""
import json
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def packs_keys(config_path):
    """Return the first-level keys under the top-level `packs:` mapping."""
    with open(config_path) as fh:
        config = yaml.safe_load(fh) or {}
    packs = config.get("packs") or {}
    return list(packs.keys())


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
