# Plan: Extend `declaratii-avere` to legislatura-2020 and legislatura-2016

## Context

`declaratii-avere` (asset declarations parsed from PDF) only exists for legislatura-2024. The source data (`data/v1/declaratii/`) also only has 2024. The scraper (`scrapers/declaratii.py`) already supports any `leg=` parameter, and `run_declaratii.py` even has `ALL_LEGS = [2024, 2020]` — someone planned for 2020 but never executed the bootstrap. 2016 is missing from `ALL_LEGS`. A secondary issue: `build_declaratii_avere.py` is entirely absent from `refresh_all.py`, so even 2024 isn't regenerated daily.

## Changes

### 1. `scripts/run_declaratii.py` — add 2016 to `ALL_LEGS`

Line 30:
```python
# before
ALL_LEGS = [2024, 2020]
# after
ALL_LEGS = [2024, 2020, 2016]
```

Also update the docstring on line 8: `# 2024 + 2020 + 2016`.

### 2. `scripts/build_declaratii_avere.py` — add `--all` flag

In `main()` (line 298), mirror the pattern from `run_declaratii.py`:

```python
ALL_LEGS = [2024, 2020, 2016]  # add near top of file, after SCRAPER_VERSION

# in main():
parser.add_argument("--all", action="store_true", help="Build 2024 + 2020 + 2016")

# replace the single-run body with:
legs = ALL_LEGS if args.all else [args.leg]
for leg in legs:
    # existing body (decl_file check, PDF_CACHE.mkdir, out_dir, loop, summaries write)
```

The existing per-leg logic doesn't need to change — just wrap it in a loop.

### 3. `scripts/refresh_all.py` — add `declaratii-avere` stage

After the `declaratii` stage (line 46), add:

```python
("declaratii-avere", ["python", "scripts/build_declaratii_avere.py", "--leg", "2024", "--verbose"], True),
```

Mark it as a derivat (`True`) since it consumes `data/v1/declaratii/`.

## Bootstrap (one-time run, must execute on the self-hosted Romania runner)

After the code changes are pushed:

```bash
# Scrape the declaration PDF lists for 2020 + 2016 (fast, ~1s each)
python scripts/run_declaratii.py --leg 2020 --verbose
python scripts/run_declaratii.py --leg 2016 --verbose

# Parse PDFs (slow — downloads all PDFs; incremental, resumable)
python scripts/build_declaratii_avere.py --leg 2020 --verbose
python scripts/build_declaratii_avere.py --leg 2016 --verbose
```

This is the only step that requires the self-hosted runner (cdep.ro geo-blocks cloud runners).

## Verification

1. After `run_declaratii.py --leg 2020`: confirm `data/v1/declaratii/legislatura-2020.json` exists and has >300 deputies.
2. After `run_declaratii.py --leg 2016`: confirm `data/v1/declaratii/legislatura-2016.json` exists similarly.
3. After `build_declaratii_avere.py --leg 2020 --limit 5`: check that `data/v1/declaratii-avere/legislatura-2020.json` exists with 5 summaries and `data/v1/declaratii-avere/legislatura-2020/` contains 5 detail files.
4. Run `PYTHONPATH=. python scripts/validate_data.py` — passes without errors.
5. Confirm `refresh_all.py` now includes `declaratii-avere` in its output list.
