# Deployment gate

The `CI` workflow gates every PR into `prod`: it scans this repo against
`codeql-config.yml` and asserts the config still produces live coverage.

## Checks

1. **Matrix derived from `codeql-config.yml`** — the `packs:` keys, mapped via
   `languageMap`. A key with no entry or no floor block fails the job, so a new
   language cannot ship without a test.
2. **Query-count floor** — rules loaded, read from this run's SARIF. Catches
   `query-filters` over-excluding.
3. **Expected rule ids loaded** — catches a pack that installs but skips its
   queries, and a CLI bump that drops one.

All floors live in `gate/config.json`, so changing one is a reviewed diff.

Whether a given query is any good is tested in `codeql-pack` (unit tests and
fixtures). No fixtures here — that would be a third copy.

## The required check

Make **`Deployment gate`** the required status check on `prod`. Its name is
stable across the derived matrix; it is red if any leg failed.

## Changing a floor

Edit `gate/config.json` and open a PR. Each leg uploads its SARIF as a
`sarif-<language>` artifact — download it to read the loaded rule ids.

## Adding a language

Add the `packs:` key, then give it a block in `gate/config.json`. Actions is
already blocked out, pending PR #19.

`derive-matrix.py` runs locally (`python3 gate/derive-matrix.py`); the scan
itself needs CI.
