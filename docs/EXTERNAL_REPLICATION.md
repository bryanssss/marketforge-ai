# Independent External Benchmark Replication

MarketForge 0.5 includes a neutral ledger analyser for independent forecast comparisons.
It does not require the external researcher to use MarketForge's internal benchmark runner.

## Ledger format

Provide one CSV row per model and forecast origin:

```csv
origin,model,actual,prediction
2026-01-01T00:00:00Z,candidate,101.0,100.7
2026-01-01T00:00:00Z,comparator,101.0,100.2
```

The `actual` value must match between both models at each origin. The analyser joins rows by
origin, calculates absolute terminal log-return errors, runs a Diebold–Mariano comparison and
creates a moving-block bootstrap confidence interval for the paired loss difference.

## Command line

```bash
python scripts/replicate_external.py external_ledger.csv \
  --candidate candidate \
  --comparator comparator \
  --bootstrap-samples 5000 \
  --block-size 5 \
  --output replication_result.json
```

## API

`POST /api/replications/analyse` accepts the CSV as `file` and a JSON `settings_json` form field.

## What this tool does not prove

The analyser cannot prove that:

- the dataset was genuinely untouched;
- a model's training cut-off is known;
- the supplied predictions were created before outcomes were observed;
- the selected origins or metrics were preregistered;
- the ledger contains every attempted forecast.

A strong independent replication should publish its protocol, source revisions, model hashes,
data hashes, complete prediction ledger and all failed or missing runs.
