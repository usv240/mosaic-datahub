# Bring your own data

Everything else in this repository runs on committed fixtures, which shows the mechanism works but not that it would find anything in *your* export. `mosaic measure` closes that gap: point it at a delimited file you supply and it applies the same aggregate-only rule the scenarios use.

```powershell
uv run mosaic measure --csv <your-file>.csv --columns col_a,col_b,col_c
```

Nothing is uploaded, nothing is written back, and no row ever leaves the process.

## Try it on the committed samples

Three synthetic files, chosen so the tool has to reach three different verdicts. All values are generated; no file describes a real person.

| File | Measure these columns | Verdict | Why |
|---|---|---|---|
| `risky_member_export.csv` | `zip5,birth_date,gender` | `validated_critical` (exit 3) | Precise ZIP, full birth date, and gender make every one of 240 people unique |
| `safe_member_export.csv` | `region,age_band,gender` | `validated_low` (exit 0) | The same population generalized — smallest group is 5 |
| `borderline_partner_audience.csv` | `region,age_band,device_type` | `validated_elevated` (exit 0) | Mostly large groups with a thin tail of rare combinations |

```powershell
uv run mosaic measure --csv examples/bring-your-own-data/risky_member_export.csv --columns zip5,birth_date,gender
uv run mosaic measure --csv examples/bring-your-own-data/safe_member_export.csv  --columns region,age_band,gender
uv run mosaic measure --csv examples/bring-your-own-data/borderline_partner_audience.csv --columns region,age_band,device_type
```

The first and second files hold the same 240 people. The only difference is generalization: precise ZIP becomes region, exact birth date becomes an age band. Watch the smallest group move from **1** to **5** — that is the same intervention `mosaic generate-remediation` writes as dbt code.

## Try it on public data

Any CSV with a header row works. Two that are easy to obtain:

**UCI Adult** — 32,561 census-derived records, the dataset behind [`evidence/external/uci-adult-proof.json`](../../evidence/external/uci-adult-proof.json).

```powershell
curl -o adult.csv https://archive.ics.uci.edu/static/public/2/adult.zip   # unzip adult.data, add a header row
uv run mosaic measure --csv adult.csv --columns age,education,marital-status,occupation,sex,native-country
```

**Any export you already have.** A customer list, an event log, a survey extract. Name any two or more columns that a person could plausibly be recognised by.

## What it does and does not do

`measure` answers *"how identifying is this combination?"* It does **not** discover which columns are quasi-identifiers — that is what `mosaic discover` does against DataHub column lineage, and it is the part of Mosaic that needs a catalog:

```powershell
uv run mosaic discover --server http://localhost:8080 --urn "<your-dataset-urn>"
```

Together they let you test both halves on your own inputs: `discover` finds the combination from your graph, `measure` proves how exposed it is.

## What comes back

Counts only:

```json
{
  "status": "validated_critical",
  "metrics": {
    "total_records": 240,
    "distinct_combinations": 240,
    "minimum_k": 1,
    "percent_below_5": 100.0,
    "class_size_distribution": {"1": 240}
  },
  "privacy": { "raw_person_rows_returned": 0 }
}
```

**No cell value from your file appears in the output** — not in the metrics, not in the reason, not in the digest. Equivalence-class values *are* the identifying combination, so echoing them back would leak precisely what the tool exists to find. A regression test asserts this against every value in the sample file.

Exit code `3` marks a critical policy result; `2` means the input was rejected. Thresholds come from `.mosaic/privacy-policy.yml` and are organization policy, not a legal conclusion.
