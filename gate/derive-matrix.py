#!/usr/bin/env python3
"""Derive the CodeQL scan-language matrix strictly from the packs: keys of
codeql-config.yml, mapped through gate/config.json's languageMap.

Emits `matrix=<json>` to $GITHUB_OUTPUT (or stdout when run locally). Fails if a
packs key has no languageMap entry or no per-language floor block, so a new pack
language cannot be added without also gaining a test in the gate.

Parses the config with PyYAML (preinstalled on ubuntu-latest runners) rather
than a hand-rolled scanner — the fail-closed key->floor check below is the part
that matters; YAML edge cases are PyYAML's problem, not ours.
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
