# Deployment gate

The `CI` workflow is the deployment gate for this central config. Every PR into
`prod` runs it E2E against `codeql-config.yml` and must pass before the config
change ships to every consumer.

## What it checks

1. **Matrix is derived from `codeql-config.yml`** — `derive-matrix.py` reads the
   `packs:` keys and maps them to scan languages via `config.json`'s
   `languageMap`. A packs key with no `languageMap` entry, or no per-language
   block in `config.json`, fails the `Derive matrix` job. You cannot add a pack
   language without also giving it a floor and fixtures here.
2. **Query-count floor** — `assert.py` counts the rules the scan actually loaded
   (from this run's SARIF, not a baseline-filtered alert count) and fails below
   `queryCountFloor`. This is the R1 silent-zero-coverage guard.
3. **Expected custom rule ids** — when a custom pack is pinned, its rule ids must
   appear in the loaded set (`expectedRuleIds`).
4. **Fixture behaviour** — a known-bad fixture in `gate/fixtures/<lang>/bad/`
   must produce ≥1 finding for its named rule, and the known-good twin in
   `good/` must stay completely silent.

`config.json` is the single reviewed surface for all floors and expectations —
bumping a floor is a diff in a PR, never a magic number in the workflow.

## The required check

Make **`Deployment gate`** (the stable summary job) the required status check on
the `prod` ruleset. Its name does not change with the derived matrix; it is red
if the derivation or any language leg failed.

## Bumping a floor / adding expected rule ids

1. Edit `gate/config.json` (`queryCountFloor` and/or `expectedRuleIds`).
2. Open a PR; the gate re-runs and either confirms or rejects the new floor.
3. The SARIF for each leg is uploaded as a `sarif-<language>` artifact — download
   it to read the exact loaded rule ids and finding locations.

## Adding a language (e.g. when the `actions:` packs key lands)

1. Add the `actions:` key to `codeql-config.yml` `packs:` (this is PR #19).
2. `config.json` already carries the `actions` block. Floor is **16, not 17**:
   the built-in Actions suite resolves 17 queries, but this config's
   `query-filters` exclude `actions/missing-workflow-permissions`, leaving 16
   (measured by the `security-canaries` run against `codeql-config.yml@prod`).
   Once the custom pack pins, raise to **19** (16 built-in + 3 custom) and
   populate `expectedRuleIds`.
3. Actions fixtures live under `gate/fixtures/actions/*/​.github/workflows/` —
   nested so the extractor sees them via `--source-root` while GitHub never runs
   them (only the repo-root `.github/workflows/` executes).

## Local checks

- `python3 gate/derive-matrix.py` — prints the matrix it would emit.
- The scan itself only runs in CI (it needs the CodeQL CLI + the published
  packs). Tune floors and fixtures by reading the uploaded SARIF artifacts.
