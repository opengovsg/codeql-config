# Deployment gate

The `CI` workflow is the deployment gate for this central config. Every PR into
`prod` runs it E2E against `codeql-config.yml` and must pass before the config
change ships to every consumer.

## What it checks

1. **Matrix is derived from `codeql-config.yml`** — `derive-matrix.py` reads the
   `packs:` keys and maps them to scan languages via `config.json`'s
   `languageMap`. A packs key with no `languageMap` entry, or no per-language
   block in `config.json`, fails the `Derive matrix` job. You cannot add a pack
   language without also giving it a floor here.
2. **Query-count floor** — `assert.py` counts the rules the scan actually loaded
   (from this run's SARIF, not a baseline-filtered alert count) and fails below
   `queryCountFloor`. Catches `query-filters` over-excluding.
3. **Expected custom rule ids** — the pinned packs' rule ids must appear in the
   loaded set. Catches a pack that installs but silently skips its queries, and
   a CLI bump that drops one.

A `paths-ignore` that guts the scan needs no assertion: this repo has a single
JS/TS source file, so excluding it makes CodeQL itself fail loudly ("no source
code seen", exit 32) before any assertion runs. Measured on two RED branches,
not assumed — an assertion that can never fire is worse than no assertion.

`config.json` is the single reviewed surface for all floors and expectations —
bumping a floor is a diff in a PR, never a magic number in the workflow.

## Scope — what this gate does NOT test

Whether an individual query is any good — does it fire on bad code, does it stay
quiet on good code — is a question about the **query**, and it is answered in
`codeql-pack` by its CodeQL unit tests (`<pack>/tests/`) and its positive and
negative fixtures (`scripts/preview`). This repo owns the **config**, so it
asserts only that the config produces live coverage. Deliberately no fixtures
here: they would be a third copy of an assertion that already has a home.

## The required check

Make **`Deployment gate`** (the stable summary job) the required status check on
the `prod` ruleset. Its name does not change with the derived matrix; it is red
if the derivation or any language leg failed.

## Bumping a floor / adding expected rule ids

1. Edit `gate/config.json`.
2. Open a PR; the gate re-runs and either confirms or rejects the new floor.
3. The SARIF for each leg is uploaded as a `sarif-<language>` artifact — download
   it to read the exact loaded rule ids.

## Adding a language (e.g. when the `actions:` packs key lands)

1. Add the `actions:` key to `codeql-config.yml` `packs:` (this is PR #19).
2. `config.json` already carries the `actions` block. Floor is **16, not 17**:
   the built-in Actions suite resolves 17 queries, but this config's
   `query-filters` exclude `actions/missing-workflow-permissions`, leaving 16
   (measured by the canary run against `codeql-config.yml@prod`). Once the
   custom pack pins, raise to **19** (16 built-in + 3 custom) and populate
   `expectedRuleIds`.

## Local checks

- `python3 gate/derive-matrix.py` — prints the matrix it would emit.
- The scan itself only runs in CI (it needs the CodeQL CLI + the published
  packs). Tune floors by reading the uploaded SARIF artifacts.
