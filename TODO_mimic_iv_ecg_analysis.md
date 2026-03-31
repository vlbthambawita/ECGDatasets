# MIMIC-IV ECG Dataset Analysis — Implementation Plan

## Goal

Build a configurable Python analysis script for the MIMIC-IV ECG (Diagnostic Electrocardiogram Matched Subset v1.0) dataset that produces:
1. A visual interactive HTML report (D3.js charts) saved in `docs/analysis/mimic_iv_ecg/report.html`
2. JSON data files in `docs/analysis/mimic_iv_ecg/data/` consumed by the D3 charts
3. Update `docs/index.html` to add a "View Report" link for MIMIC-IV ECG

---

## Dataset Facts (from exploration)

- **Location:** `/work/vajira/DATA/SEARCH/MIMIC_IV_ECG_raw_v1/mimic-iv-ecg-diagnostic-electrocardiogram-matched-subset-1.0/`
- **Records:** 800,035 ECG studies across 160,862 unique patients
- **Format:** WFDB (.hea header + .dat binary), 12-lead, 500 Hz, 10 seconds (5000 samples per lead)
- **License:** ODC Open Database License (ODbL)

### Top-level files

```
1.0/
├── record_list.csv                            # 800,035 rows — all ECG records with paths
├── machine_measurements.csv                   # 789,481 rows × 33 cols — automated measurements + text reports
├── machine_measurements_original.csv          # 789,481 rows — pre-processed original measurements
├── machine_measurements_data_dictionary.csv   # 18 rows — variable descriptions
├── waveform_note_links.csv                    # 609,272 rows — links ECGs to MIMIC-IV clinical notes
├── RECORDS                                    # 1000 patient group directory names (p1000–p1999)
├── SHA256SUMS.txt                             # file integrity checksums
├── LICENSE.txt                                # ODC ODbL full text
└── files/
    └── pXXXX/                                 # 1000 patient-group folders (p1000–p1999)
        └── pNNNNNNNN/                         # individual patient directory (subject_id)
            └── sNNNNNNNN/                     # study directory (study_id)
                ├── NNNNNNNN.hea               # WFDB header (text)
                └── NNNNNNNN.dat               # WFDB signal (binary, 16-bit)
```

### Key CSV columns

**`record_list.csv`** — 5 columns:
- `subject_id`, `study_id`, `file_name`, `ecg_time`, `path`

**`machine_measurements.csv`** — 33 columns:
- `subject_id`, `study_id`, `cart_id`, `ecg_time`
- `report_0` … `report_17` — machine-generated text diagnostic reports (variable number of fields, blank when absent)
- `bandwidth`, `filtering`
- `rr_interval`, `p_onset`, `p_end`, `qrs_onset`, `qrs_end`, `t_end` — interval measurements (ms)
- `p_axis`, `qrs_axis`, `t_axis` — electrical axes (degrees)

**`waveform_note_links.csv`** — 6 columns:
- `subject_id`, `study_id`, `waveform_path`, `note_id`, `note_seq`, `charttime`

### WFDB header fields (per record)
- 12 leads: I, II, III, aVR, aVF, aVL, V1–V6
- Sampling rate: 500 Hz
- Duration: 10 s (5000 samples per lead)
- Resolution: 200 ADC units/mV, 16-bit signed integer

---

## Deliverables

```
analysis/
└── mimic_iv_ecg/
    ├── config.yaml          ← analysis + HF upload configuration
    ├── clean_records.csv    ← gitignored; pushed to HF Dataset by Phase 19 (HF_DATASET_TOKEN from .env)
    ├── train.csv            ← gitignored; single column: study_id; pushed to HF Dataset by Phase 21
    ├── validate.csv         ← gitignored; single column: study_id; pushed to HF Dataset by Phase 21
    ├── test.csv             ← gitignored; single column: study_id; pushed to HF Dataset by Phase 21
    └── split_summary.json   ← gitignored; also copied to docs/analysis/mimic_iv_ecg/data/

docs/
└── analysis/
    └── mimic_iv_ecg/
        ├── data/            ← JSON data files consumed by D3 charts
        │   ├── dataset_summary.json
        │   ├── record_coverage.json
        │   ├── temporal_distribution.json
        │   ├── studies_per_patient.json
        │   ├── measurement_stats.json
        │   ├── measurement_missing.json
        │   ├── interval_distributions.json
        │   ├── axis_distributions.json
        │   ├── report_text_freq.json
        │   ├── cart_usage.json
        │   ├── bandwidth_filtering.json
        │   ├── note_link_coverage.json
        │   ├── waveform_header_stats.json
        │   ├── lead_completeness.json
        │   ├── signal_quality.json
        │   ├── clean_records_summary.json
        │   └── split_summary.json
        └── report.html      ← self-contained report (D3 charts inline, no CDN)
```

> **Same pattern as PTB-XL and PTB-XL+:** `analysis/<dataset>/` holds only config + clean_records.csv; `docs/analysis/<dataset>/` holds the report and JSON data served via GitHub Pages.

> **Scripts:**
> ```
> scripts/
> ├── analyse_mimic_iv_ecg.py            ← main analysis script (20 phases)
> ├── report_template_mimic_iv_ecg.html  ← Jinja2 + D3 report template
> └── vendor/d3.min.js                   ← bundled D3 v7 (no CDN)
> ```
> **Secrets:** `.env` (gitignored) holds `HF_DATASET_TOKEN`; copy from `.env.example`.

---

## Configuration File

`analysis/mimic_iv_ecg/config.yaml`:

```yaml
dataset:
  root: /work/vajira/DATA/SEARCH/MIMIC_IV_ECG_raw_v1/mimic-iv-ecg-diagnostic-electrocardiogram-matched-subset-1.0
  records_file: RECORDS

  csv:
    record_list:          record_list.csv
    measurements:         machine_measurements.csv
    measurements_orig:    machine_measurements_original.csv
    data_dictionary:      machine_measurements_data_dictionary.csv
    note_links:           waveform_note_links.csv

  waveforms:
    root: files

output:
  report_dir:    docs/analysis/mimic_iv_ecg
  data_dir:      docs/analysis/mimic_iv_ecg/data
  report_html:   docs/analysis/mimic_iv_ecg/report.html
  clean_records: analysis/mimic_iv_ecg/clean_records.csv   # gitignored; pushed to HF Dataset by Phase 19

analysis:
  top_n_reports:          40      # top N machine-report phrases
  top_n_carts:            30      # top N ECG cart IDs
  max_records:            null    # null = all; set integer (e.g. 5000) for fast test runs
  sample_waveforms:       200     # .hea files to read for header stats
  sample_signal_quality:  2000    # .dat files to read for flat/missing lead detection
  missing_threshold_pct:  5.0     # flag measurements with >N% missing values

huggingface:
  dataset_repo: vlbthambawita/ecg-metadata-curated
  path_in_repo: mimic_iv_ecg/clean_records.csv
  # Token read from HF_DATASET_TOKEN in .env — never put the token value here

signal_analysis:
  flat_threshold:       0.01   # mV; leads with std below this are "flat"
  nan_count_threshold:  1      # samples with >= this many NaN values are flagged
  check_500hz:          true   # MIMIC-IV ECG is always 500 Hz; set false to skip

clean_record_criteria:
  require_all_12_leads: true
  no_flat_leads:        true
  no_nan_in_leads:      true
  no_missing_metadata:
    - ecg_time          # recording datetime must be present
    - rr_interval       # at least one interval measurement must be non-null
    - report_0          # at least the first machine-generated report phrase must be present
  # Note: MIMIC-IV ECG has no explicit quality-flag annotations (no equivalent of PTB-XL's
  # baseline_drift / static_noise / burst_noise / electrodes_problems flags).
  # Signal quality filtering is purely derived from flat_threshold and nan_count_threshold above.

splits:
  # ── Filtering (applied to clean_records.csv before splitting) ────────────────
  filters:
    ecg_time_year_min:        null    # inclusive lower bound on recording year (MIMIC dates are shifted ~2100s)
    ecg_time_year_max:        null    # inclusive upper bound on recording year
    rr_interval_min:          400     # ms — drop records with RR interval below this (extreme bradycardia)
    rr_interval_max:          1500    # ms — drop records with RR interval above this (extreme bradycardia)
    qrs_axis_min:             null    # degrees — null = no filter
    qrs_axis_max:             null
    require_report_phrase:    []      # keep records containing ANY of these phrases (substring, case-insensitive); [] = no filter
    exclude_report_phrase:    []      # drop records containing ANY of these phrases; [] = no filter
    max_studies_per_patient:  null    # null = keep all; integer = cap per-patient studies (random sample, seeded)

  # ── Splitting ────────────────────────────────────────────────────────────────
  strategy:
    split_by:    patient      # "patient" = whole-patient assignment (no patient spans splits)
    train_pct:   0.80
    val_pct:     0.10
    test_pct:    0.10         # must sum to 1.0
    stratify_by: null         # null = unstratified random; column name from measurements (e.g. "qrs_axis") for stratified split
    stratify_bins: 5          # number of equal-width bins when stratify_by is a continuous column
    random_seed: 42

  # ── Output ───────────────────────────────────────────────────────────────────
  output:
    train:    analysis/mimic_iv_ecg/train.csv        # gitignored; pushed to HF by Phase 21
    validate: analysis/mimic_iv_ecg/validate.csv
    test:     analysis/mimic_iv_ecg/test.csv
    summary:  analysis/mimic_iv_ecg/split_summary.json   # also copied to docs/analysis/mimic_iv_ecg/data/

  huggingface:
    train_path:    mimic_iv_ecg/train.csv
    validate_path: mimic_iv_ecg/validate.csv
    test_path:     mimic_iv_ecg/test.csv
    summary_path:  mimic_iv_ecg/split_summary.json
```

---

## Script Structure

**File:** `scripts/analyse_mimic_iv_ecg.py`

### Phases

#### Phase 1 — Load & Validate Config
- Parse `config.yaml` (path passed as CLI arg: `--config`)
- Resolve all paths relative to repo root or as absolute
- Validate that all expected CSV files and `files/` directory exist; warn on missing

#### Phase 2 — Load Data
- Load `record_list.csv` → `records_df` (800K rows)
- Load `machine_measurements.csv` → `meas_df` (789K rows)
- Load `machine_measurements_original.csv` → `meas_orig_df`
- Load `machine_measurements_data_dictionary.csv` → `dict_df`
- Load `waveform_note_links.csv` → `links_df`
- Parse `ecg_time` columns as datetime

#### Phase 3 — Dataset Summary
Compute and serialize to `data/dataset_summary.json`:
- Total records in `record_list.csv`
- Total unique patients (`subject_id`)
- Total unique studies (`study_id`)
- Records with machine measurements (intersection of record_list and measurements)
- Records with note links
- Records with waveform files on disk
- Date range of recordings (min/max `ecg_time`)
- Number of patient-group folders (`p1000–p1999`)

#### Phase 4 — Record Coverage Analysis
Compare what is listed in `record_list.csv` vs. what has machine measurements vs. what has note links vs. what exists on disk (scan a sample of the `files/` tree for .hea/.dat pairs).

Serialize to `data/record_coverage.json`:
- Per-source counts: record_list, measurements, note_links, waveform_files
- Missing measurement records (in record_list but not in measurements)
- Missing note-link records (in record_list but not in note_links)

#### Phase 5 — Temporal Distribution
Using `ecg_time` from `record_list.csv`:
- Count ECG studies per year
- Count ECG studies per month (aggregated across all years)
- Count ECG studies per hour-of-day (to detect clinical patterns)
- Count ECG studies per day-of-week

Serialize to `data/temporal_distribution.json`:
- `{by_year: [{year, count}], by_month: [{month, count}], by_hour: [{hour, count}], by_dow: [{day, count}]}`

#### Phase 6 — Studies-per-Patient Distribution
Using `record_list.csv`, group by `subject_id`:
- Count studies per patient
- Compute: min, max, mean, median, p25, p75, p95
- Bin counts into histogram buckets (1, 2–5, 6–10, 11–20, 21–50, 50+)
- Identify the maximum number of studies for a single patient

Serialize to `data/studies_per_patient.json`:
- `{stats: {min, max, mean, median, p25, p75, p95}, histogram: [{bucket, count}]}`

#### Phase 7 — Machine Measurement Statistics
For each numeric column in `machine_measurements.csv` (`rr_interval`, `p_onset`, `p_end`, `qrs_onset`, `qrs_end`, `t_end`, `p_axis`, `qrs_axis`, `t_axis`):
- Compute mean, std, min, p25, p50, p75, max, count, missing_pct

Serialize to `data/measurement_stats.json`:
- List of `{field, description, unit, mean, std, min, p25, p50, p75, max, count, missing_pct}`

#### Phase 8 — Missing Measurement Values
For every column in `machine_measurements.csv`, compute missing % (null/NaN).
Flag columns above `missing_threshold_pct`.

Serialize to `data/measurement_missing.json`:
- List of `{field, description, missing_pct, flagged}` sorted by missing_pct descending

#### Phase 9 — Interval & Axis Distributions
For key interval fields (`rr_interval`, `p_end - p_onset`, `qrs_end - qrs_onset`, `t_end - qrs_end`) compute histogram buckets (50 bins).

Derive computed fields:
- **PR interval:** `qrs_onset - p_onset`
- **QRS duration:** `qrs_end - qrs_onset`
- **QT interval:** `t_end - qrs_onset`

Serialize to `data/interval_distributions.json`:
- `{field: {label, unit, bins: [{x0, x1, count}]}}`

Separately for axes (`p_axis`, `qrs_axis`, `t_axis`), compute histogram (-180 to +180, 36 bins).

Serialize to `data/axis_distributions.json`:
- `{axis: {bins: [{x0, x1, count}]}}`

#### Phase 10 — Machine Report Text Frequency
From `report_0` … `report_17` in `machine_measurements.csv`:
- Concatenate all report fields per record into a single list of non-null strings
- Count occurrence frequency of each unique report phrase (exact string match after stripping whitespace)
- Compute what fraction of all records carry each phrase
- Serialize top-N phrases to `data/report_text_freq.json`:
  - `{total_records, phrases: [{text, count, pct}]}` sorted by count descending

#### Phase 11 — ECG Cart Usage
From `cart_id` in `machine_measurements.csv`:
- Count unique cart IDs
- Compute studies-per-cart distribution (histogram)
- Top-N most-used carts
- Serialize to `data/cart_usage.json`:
  - `{total_carts, top_carts: [{cart_id, count, pct}], histogram: [{bucket, count}]}`

#### Phase 12 — Bandwidth & Filtering Profiles
From `bandwidth` and `filtering` in `machine_measurements.csv`:
- Count occurrences of each unique `bandwidth` string
- Count occurrences of each unique `filtering` string
- Serialize to `data/bandwidth_filtering.json`:
  - `{bandwidth: [{value, count, pct}], filtering: [{value, count, pct}]}`

#### Phase 13 — Waveform–Note Link Coverage
From `waveform_note_links.csv`:
- Total ECG-note links
- Unique patients with at least one note link
- Notes-per-ECG distribution (histogram: 1, 2–5, 6–10, >10)
- ECG records in `record_list.csv` without any note link
- Serialize to `data/note_link_coverage.json`:
  - `{total_links, records_with_links, records_without_links, patients_with_links, histogram: [{bucket, count}]}`

#### Phase 14 — Waveform Header Stats (sample)
Read `sample_waveforms` random `.hea` files from `files/`:
- Verify all have 12 leads (I, II, III, aVR, aVF, aVL, V1–V6)
- Confirm sampling rate (expected: 500 Hz)
- Confirm sample count (expected: 5000)
- Collect any variation in resolution (ADC gain) or bit depth
- Count how many samples have exactly 12 leads vs. fewer/more

Serialize to `data/waveform_header_stats.json`:
- `{sample_size, leads_12_count, sampling_rates: {value: count}, sample_counts: {value: count}, resolutions: {value: count}, bit_depths: {value: count}}`

#### Phase 15 — Lead Completeness (full scan of all .hea files)
Scan **every** `.hea` file in `files/` (not just a sample) and parse the declared lead names:
- Count records with exactly 12 leads vs. fewer or more
- For records with fewer than 12, record which leads are present and which are absent
- Compute per-lead absence rate: for each of the 12 standard leads, what fraction of records is it missing?
- Count records where the lead order differs from the expected standard (I, II, III, aVR, aVF, aVL, V1–V6)

Serialize to `data/lead_completeness.json`:
```json
{
  "total_scanned": 800035,
  "records_with_12_leads": 799800,
  "records_with_fewer_leads": 235,
  "records_with_more_leads": 0,
  "per_lead_absence": {
    "I":   {"absent_count": 12, "absent_pct": 0.0015},
    "II":  {"absent_count":  5, "absent_pct": 0.0006},
    ...
  },
  "nonstandard_lead_order_count": 10,
  "incomplete_records": [
    {"study_id": 12345678, "leads_present": ["I","II","III"], "leads_missing": ["aVR","aVF","aVL","V1","V2","V3","V4","V5","V6"]}
  ]
}
```
> Note: `.hea` files are small text files (~600 bytes each); scanning all 800K is I/O-bound but feasible with `tqdm` progress. Use `wfdb.rdheader()` or plain text parsing. Limit `incomplete_records` list to first 500 cases to keep the JSON size reasonable.

#### Phase 16 — Signal Quality: Flat & NaN Lead Detection (sampled)
Read `sample_signal_quality` randomly selected `.dat` files (via `wfdb.rdsamp()`) and for each record inspect every lead signal using the thresholds from `signal_analysis` in config:

**Flat-line detection:** a lead is flat if `np.std(signal) < signal_analysis.flat_threshold` (default 0.01 mV).

**NaN/dropout detection:** a lead is flagged if it contains `>= signal_analysis.nan_count_threshold` NaN samples (default 1).

**Clipping detection:** a lead is clipped if more than 1% of samples equal the physical signal min or max (heuristic for ADC rail saturation).

Per record, flag any leads that are flat, NaN-affected, or clipped.

Serialize to `data/signal_quality.json`:
```json
{
  "sample_size": 2000,
  "records_with_any_issue": 18,
  "per_lead_issues": {
    "I":   {"flat_count": 2,  "flat_pct": 0.10, "dropout_count": 0, "clip_count": 1},
    "II":  {"flat_count": 0,  "flat_pct": 0.00, "dropout_count": 0, "clip_count": 0},
    ...
  },
  "issue_type_counts": {
    "flat":    {"records": 12, "lead_instances": 15},
    "dropout": {"records":  4, "lead_instances":  6},
    "clipped": {"records":  5, "lead_instances":  8}
  },
  "flagged_records": [
    {"study_id": 12345678, "issues": {"V1": ["flat"], "aVL": ["dropout"]}}
  ]
}
```
> Limit `flagged_records` list to first 200 cases. Because this reads binary `.dat` files, use the `sample_signal_quality` cap (default 2000) to keep runtime reasonable — full 800K signal scan would take hours.

#### Phase 17 — Clean Record Identification
Apply all `clean_record_criteria` from config to the full dataset and produce a list of study IDs that pass every criterion. This mirrors the `clean_records.csv` produced by the PTB-XL pipeline.

**Criteria applied (all must pass):**

| Criterion | Source | How to check |
|-----------|--------|-------------|
| `require_all_12_leads` | Phase 15 `.hea` scan | `lead_completeness.json` — `leads_missing` is empty |
| `no_flat_leads` | Phase 16 signal quality | `signal_quality.json` — no lead flagged `"flat"` |
| `no_nan_in_leads` | Phase 16 signal quality | `signal_quality.json` — no lead flagged `"nan"` |
| `no_missing_metadata: ecg_time` | `record_list.csv` | `ecg_time` is not null |
| `no_missing_metadata: rr_interval` | `machine_measurements.csv` | `rr_interval` is not null |
| `no_missing_metadata: report_0` | `machine_measurements.csv` | `report_0` is not null |

> **Important:** Phase 16 only samples `sample_signal_quality` records. For the clean-records pass, re-run signal quality checks on **all** records (or accept that the flat/NaN exclusion is based on the full `.hea` scan from Phase 15 plus sampled signal data). Document clearly in the JSON which criteria were applied exhaustively vs. from a sample.

Serialize to `data/clean_records_summary.json`:
```json
{
  "total_records":          800035,
  "passed_all_criteria":    795000,
  "excluded_missing_leads": 235,
  "excluded_flat_leads":    120,
  "excluded_nan_leads":     45,
  "excluded_missing_ecg_time":    12,
  "excluded_missing_rr_interval": 8800,
  "excluded_missing_report_0":    0,
  "signal_quality_source":  "sampled (2000 records) — flat/NaN exclusions are estimates",
  "criteria_applied": { ... }
}
```

Write `clean_records.csv` with columns: `study_id, subject_id, ecg_time, path` — one row per record that passed all criteria.

#### Phase 18b — Stratified Train / Validate / Test Split

After `clean_records.csv` is written by Phase 17/18, apply configurable filtering and patient-level stratified splitting to produce three CSVs.

**Filtering** (`splits.filters` in config) — drop rows from `clean_records.csv` that fail any enabled filter:

| Filter key | Column source | Behaviour |
|---|---|---|
| `ecg_time_year_min` / `ecg_time_year_max` | `ecg_time` | Keep records where `year` is within the specified range (inclusive) |
| `rr_interval_min` / `rr_interval_max` | `machine_measurements.csv` | Keep records within RR interval bounds (ms) |
| `qrs_axis_min` / `qrs_axis_max` | `machine_measurements.csv` | Keep records within QRS axis bounds (degrees) |
| `require_report_phrase` | `machine_measurements.csv` | Keep records where any `report_0…report_17` field matches at least one phrase in the list (substring, case-insensitive) |
| `exclude_report_phrase` | `machine_measurements.csv` | Drop records where any report field matches any phrase in the list |
| `max_studies_per_patient` | `record_list.csv` | If a patient has more than N studies, sample N randomly (deterministic via `random_seed`) |

**Splitting** (`splits.strategy` in config):

- `split_by: patient` (default, required) — patients are assigned to splits whole; no patient appears in more than one split
- `train_pct`, `val_pct`, `test_pct` — must sum to 1.0
- `stratify_by` — optional column to stratify on (e.g. `qrs_axis_bucket`, `year_bucket`, or `null` for unstratified random split); if not null, buckets are computed from the named column using `stratify_bins` bin edges before splitting
- `random_seed` — integer seed for reproducibility

**Output files** (gitignored; pushed to HF Dataset by Phase 21):
```
analysis/mimic_iv_ecg/
  train.csv        # single column: study_id (record IDs only — no metadata)
  validate.csv     # single column: study_id
  test.csv         # single column: study_id
  split_summary.json   # counts + filter audit trail
```

**`split_summary.json` schema:**
```json
{
  "filter_applied": {
    "ecg_time_year_min": 2100,
    "ecg_time_year_max": 2200,
    "rr_interval_min": 400,
    "rr_interval_max": 1200,
    "max_studies_per_patient": 10
  },
  "records_before_filter": 789478,
  "records_after_filter":  750000,
  "unique_patients_after_filter": 155000,
  "split_strategy": "patient",
  "stratify_by": "qrs_axis_bucket",
  "random_seed": 42,
  "splits": {
    "train":    {"records": 600000, "patients": 124000, "pct": 0.80},
    "validate": {"records":  75000, "patients":  15500, "pct": 0.10},
    "test":     {"records":  75000, "patients":  15500, "pct": 0.10}
  },
  "huggingface_urls": null
}
```

> `huggingface_urls` starts as `null` at Phase 18b write time. Phase 21 overwrites it with the three public HF download URLs after a successful upload. The report reads this field from `data/split_summary.json` (which Phase 21 also updates) so the links appear live in the rendered page.

Serialize `data/split_summary.json` (for the HTML report chart) alongside the above.

#### Phase 19 — Push clean_records.csv to HuggingFace Dataset
Read `HF_DATASET_TOKEN` from the environment (loaded automatically from `.env` via `python-dotenv` at script startup). Use `huggingface_hub.HfApi.upload_file()` to push `analysis/mimic_iv_ecg/clean_records.csv` to `vlbthambawita/ecg-metadata-curated` at `mimic_iv_ecg/clean_records.csv`. Skip with a warning if token is missing.

The file is **gitignored** — it is never committed to GitHub.

Prerequisites:
```
cp .env.example .env
# edit .env and set HF_DATASET_TOKEN=hf_...
pip install python-dotenv huggingface-hub
```

#### Phase 21 — Push train/validate/test splits to HuggingFace Dataset

After Phase 18b writes the three CSVs, upload them to `vlbthambawita/ecg-metadata-curated` using the same `HF_DATASET_TOKEN` from `.env`:

```
mimic_iv_ecg/train.csv
mimic_iv_ecg/validate.csv
mimic_iv_ecg/test.csv
mimic_iv_ecg/split_summary.json
```

Each file is uploaded with `HfApi.upload_file()`. Skip with a warning if token is missing. All four files are **gitignored**.

**After uploading**, construct the public HuggingFace download URLs for each file and write them back into `split_summary.json` and `data/split_summary.json` under a `huggingface_urls` key:

```json
"huggingface_urls": {
  "train":    "https://huggingface.co/datasets/vlbthambawita/ecg-metadata-curated/resolve/main/mimic_iv_ecg/train.csv",
  "validate": "https://huggingface.co/datasets/vlbthambawita/ecg-metadata-curated/resolve/main/mimic_iv_ecg/validate.csv",
  "test":     "https://huggingface.co/datasets/vlbthambawita/ecg-metadata-curated/resolve/main/mimic_iv_ecg/test.csv"
}
```

The URL pattern is: `https://huggingface.co/datasets/{dataset_repo}/resolve/main/{path_in_repo}` — derive from the `huggingface.dataset_repo` and `splits.huggingface.*_path` values in config so no URL is ever hardcoded.

If the token is missing and upload is skipped, set `huggingface_urls` to `null` in the JSON so the report template can conditionally render the links.

#### Phase 20 — Generate HTML Report (D3.js)
Produce a **self-contained** `report.html` (rendered from `scripts/report_template_mimic_iv_ecg.html` via Jinja2) that:
- Bundles D3 v7 inline from `scripts/vendor/d3.min.js` (no CDN)
- Inlines all JSON data blobs as JS variables (quoted keys — see PTB-XL+ fix)
- Renders all charts client-side using D3:

| Chart | Type | Data source |
|-------|------|-------------|
| Dataset summary cards | Stat cards | `dataset_summary.json` |
| Record coverage per source | Grouped bar | `record_coverage.json` |
| ECG studies by year | Line/bar chart | `temporal_distribution.json` |
| ECG studies by hour of day | Bar chart | `temporal_distribution.json` |
| Studies-per-patient histogram | Bar chart | `studies_per_patient.json` |
| Missing measurement values | Horizontal bar | `measurement_missing.json` |
| Measurement summary stats | Table | `measurement_stats.json` |
| RR interval distribution | Histogram | `interval_distributions.json` |
| PR/QRS/QT interval distributions | Histogram (tabbed) | `interval_distributions.json` |
| P/QRS/T axis distributions | Polar/bar histogram | `axis_distributions.json` |
| Machine report phrases (top-N) | Horizontal bar | `report_text_freq.json` |
| ECG cart usage (top-N) | Bar chart | `cart_usage.json` |
| Bandwidth & filter profiles | Donut/pie charts | `bandwidth_filtering.json` |
| Waveform–note link coverage | Stat cards + bar | `note_link_coverage.json` |
| Waveform header stats | Stat cards + table | `waveform_header_stats.json` |
| Lead completeness — per-lead absence rate | Horizontal bar | `lead_completeness.json` |
| Signal quality — flat/NaN/clip per lead | Grouped bar (tabbed: flat / NaN / clip) | `signal_quality.json` |
| Clean record summary — exclusions per criterion | Horizontal bar + stat cards | `clean_records_summary.json` |
| Train / Validate / Test split — record & patient counts per split | Grouped bar + stat cards; filter audit table; HuggingFace download links (train / validate / test) with fallback message when URLs are null | `split_summary.json` |

- Each chart: tooltip on hover, "Download SVG" button, stats table below with "Download CSV" button
- Sections (sidebar nav): Summary → Record Coverage → Temporal → Studies per Patient → Measurements → Report Phrases → Carts & Equipment → Note Links → Waveform Headers → Lead Completeness → Signal Quality → Clean Records → Dataset Splits
- Responsive layout, sticky sidebar nav for section jumping

---

## Update `docs/index.html`

Add a new row for MIMIC-IV ECG in the dataset table with a "View Report" link (matching existing row style):

```html
<a class="analysis-link" href="analysis/mimic_iv_ecg/report.html" target="_blank">&#128202; View Report</a>
```

Also update `README.md` to list MIMIC-IV ECG as an available dataset with its report link.

---

## Dependencies

### Python
```
wfdb>=4.1            # reading .hea headers and .dat waveforms
pandas>=2.0
numpy>=1.24
pyyaml>=6.0
tqdm>=4.65
jinja2>=3.1          # HTML report templating
python-dotenv>=1.0   # loads HF_DATASET_TOKEN from .env
huggingface-hub>=0.23  # uploads clean_records.csv to HF Dataset
```

### Front-end (bundled into report.html)
```
d3 v7     # vendored at scripts/vendor/d3.min.js — no CDN dependency
```

---

## Tasks (in order)

- [x] **T1** Create output directories: `analysis/mimic_iv_ecg/`, `docs/analysis/mimic_iv_ecg/`, `docs/analysis/mimic_iv_ecg/data/`
- [x] **T2** Write `analysis/mimic_iv_ecg/config.yaml` with all parameters above (includes `huggingface:` block for HF Dataset push)
- [x] **T3** Confirm `scripts/vendor/d3.min.js` exists (reuse from PTB-XL pipeline)
- [x] **T4** Write `scripts/analyse_mimic_iv_ecg.py`:
  - [x] T4a — CLI entry point + config loader + path validation
  - [x] T4b — Data loaders: record_list, measurements, note_links CSVs; parse ecg_time as datetime; load `.env` via `python-dotenv`
  - [x] T4c — Dataset summary → `data/dataset_summary.json`
  - [x] T4d — Record coverage analysis → `data/record_coverage.json`
  - [x] T4e — Temporal distribution (year / month / hour / dow) → `data/temporal_distribution.json`
  - [x] T4f — Studies-per-patient distribution → `data/studies_per_patient.json`
  - [x] T4g — Measurement summary statistics → `data/measurement_stats.json`
  - [x] T4h — Missing value analysis → `data/measurement_missing.json`
  - [x] T4i — Interval distributions (RR, PR, QRS, QT) → `data/interval_distributions.json`
  - [x] T4j — Axis distributions (p_axis, qrs_axis, t_axis) → `data/axis_distributions.json`
  - [x] T4k — Machine report text frequency (top-N phrases) → `data/report_text_freq.json`
  - [x] T4l — ECG cart usage → `data/cart_usage.json`
  - [x] T4m — Bandwidth & filter profiles → `data/bandwidth_filtering.json`
  - [x] T4n — Waveform–note link coverage → `data/note_link_coverage.json`
  - [x] T4o — Waveform header stats (sampled .hea reads) → `data/waveform_header_stats.json`
  - [x] T4p — Lead completeness (full .hea scan, all records) → `data/lead_completeness.json`
  - [x] T4q — Signal quality: flat/NaN/clip detection using `signal_analysis` thresholds (sampled .dat reads) → `data/signal_quality.json`
  - [x] T4r — Clean record identification using `clean_record_criteria` → `data/clean_records_summary.json` + `analysis/mimic_iv_ecg/clean_records.csv` (Phase 18)
  - [ ] T4r2 — Phase 18b: stratified train/validate/test split → `analysis/mimic_iv_ecg/{train,validate,test}.csv` (record IDs only) + `split_summary.json`; read `splits:` block from config
  - [x] T4s — Phase 19: push `clean_records.csv` to HF Dataset using `HF_DATASET_TOKEN` from `.env`
  - [ ] T4s2 — Phase 21: push `train.csv`, `validate.csv`, `test.csv` to HF Dataset; construct public HF download URLs from config; write URLs back into `split_summary.json` and `data/split_summary.json` under `huggingface_urls`; re-upload updated `split_summary.json`
  - [x] T4t — Phase 20: HTML report generator: render `scripts/report_template_mimic_iv_ecg.html` via Jinja2
- [x] **T5** Write `scripts/report_template_mimic_iv_ecg.html` (Jinja2 + D3 template):
  - [x] T5a — Sidebar nav + responsive layout (reuse PTB-XL/PTB-XL+ template structure)
  - [x] T5a2 — Dataset structure D3 collapsible tree (first section at top of page): color-coded by node type (dir/CSV/WFDB), expand/collapse all buttons, tooltip on hover, Download SVG
  - [x] T5a3 — CSV column drill-down in the dataset structure tree: each CSV node expands **downward** (as a vertical child list below the node, distinct from the horizontal tree layout) to reveal its column headings when clicked; column nodes are leaf-only (not further expandable) and styled differently (monospace pill, lighter color) from file/directory nodes

    **Column children per CSV file to hardcode in the tree data:**

    | CSV file | Columns |
    |---|---|
    | `record_list.csv` | `subject_id` · `study_id` · `file_name` · `ecg_time` · `path` |
    | `machine_measurements.csv` | `subject_id` · `study_id` · `cart_id` · `ecg_time` · `report_0` … `report_17` (18 fields) · `bandwidth` · `filtering` · `rr_interval` · `p_onset` · `p_end` · `qrs_onset` · `qrs_end` · `t_end` · `p_axis` · `qrs_axis` · `t_axis` |
    | `machine_measurements_original.csv` | same 33 columns as `machine_measurements.csv` |
    | `machine_measurements_data_dictionary.csv` | `variable` · `label` · `description` · `unit` |
    | `waveform_note_links.csv` | `subject_id` · `study_id` · `waveform_path` · `note_id` · `note_seq` · `charttime` |

    **Interaction model:**
    - First click on a CSV node → expands the horizontal tree branch as usual (existing behaviour)
    - A secondary **"cols ▾"** toggle button rendered next to the CSV node label opens/closes the column child list independently of the tree collapse; column children hang vertically below the CSV node using a `foreignObject` or a separate sub-tree layout so they do not disturb the horizontal tree geometry
    - Alternatively (simpler): treat column names as additional tree children rendered in the same horizontal D3 tree but at a fixed reduced `nodeSize` so the list fits without stretching the canvas too wide — columns are indented one level deeper than the CSV node, with a small `⬡` icon and monospace font
    - Column nodes show a tooltip with a short description (type + role) on hover:
      - `subject_id` — patient identifier (integer)
      - `study_id` — ECG study identifier (integer, primary key)
      - `ecg_time` — datetime of acquisition (date-shifted for de-identification)
      - `path` — relative path to WFDB record within `files/`
      - `report_0…report_17` — machine-generated diagnostic phrase (string, often blank)
      - `rr_interval`, `p_onset`, `p_end`, `qrs_onset`, `qrs_end`, `t_end` — interval measurement (ms, float)
      - `p_axis`, `qrs_axis`, `t_axis` — electrical axis (degrees, float)
      - `bandwidth`, `filtering` — ECG device acquisition settings (string)
      - `cart_id` — ECG cart/device identifier (string)
      - `waveform_path` — path used to link waveform to clinical note
      - `note_id`, `note_seq` — MIMIC-IV clinical note identifiers
      - `charttime` — datetime of linked clinical note
      - `variable`, `label`, `description`, `unit` — data dictionary fields
    - Column nodes are **collapsed by default**; the "Expand All" button in the section header does NOT auto-expand column children (too noisy) — they only open on explicit click of the CSV node's "cols" toggle
  - [x] T5b — Summary stat cards
  - [x] T5c — Record coverage grouped bar chart
  - [x] T5d — Temporal distribution charts (by year, by hour-of-day)
  - [x] T5e — Studies-per-patient histogram
  - [x] T5f — Measurement missing values horizontal bar
  - [x] T5g — Measurement stats table
  - [x] T5h — Interval distributions histograms (tabbed: RR / PR / QRS / QT)
  - [x] T5i — Axis distributions bar histograms (P / QRS / T axes, tabbed)
  - [x] T5j — Machine report phrase frequency horizontal bar
  - [x] T5k — Cart usage bar chart
  - [x] T5l — Bandwidth & filter donut charts
  - [x] T5m — Note link coverage cards + bar
  - [x] T5n — Waveform header stats cards + table
  - [x] T5o — Lead completeness horizontal bar (per-lead absence rate) + table of incomplete records
  - [x] T5p — Signal quality grouped bar charts (tabbed: flat / NaN / clipped) + flagged records table
  - [x] T5q — Clean records section: exclusions-per-criterion horizontal bar + stat cards
  - [x] T5r — Shared `downloadSVG()` utility + per-chart download button
  - [x] T5s — Shared `downloadTableCSV()` utility + per-table download button
  - [x] T5t — All DATA keys quoted in Jinja2 template (`"{{ key }}": {{ blob }},`) to avoid JS syntax errors
  - [ ] T5u — Dataset Splits section: stat cards (train/val/test record + patient counts), grouped bar chart, filter audit table; HuggingFace download link buttons for each split CSV (`split_summary.huggingface_urls.train` etc.); if URLs are null show a greyed-out "Not yet uploaded" badge instead
- [x] **T6** Run the script end-to-end (test with `max_records: 5000`, then full run with `null`) — 800,035 records, 789,478 clean
- [x] **T7** Verify `docs/analysis/mimic_iv_ecg/report.html` renders correctly (395 KB, all D3 charts)
- [x] **T8** Update `docs/index.html` — added MIMIC-IV ECG row with "View Report" link
- [x] **T9** Update `README.md` to list MIMIC-IV ECG as an available dataset
- [ ] **T10** Set `HF_DATASET_TOKEN` in `.env`, re-run the analysis script — Phase 19 will push `analysis/mimic_iv_ecg/clean_records.csv` (789,478 rows, ~60 MB) directly to `hf://datasets/vlbthambawita/ecg-metadata-curated/mimic_iv_ecg/clean_records.csv`
- [ ] **T12** Implement Phase 18b in `scripts/analyse_mimic_iv_ecg.py`: filtering + patient-stratified split → `train.csv`, `validate.csv`, `test.csv` (record IDs only: `study_id` column), `split_summary.json`
- [ ] **T13** Add `splits:` block to `analysis/mimic_iv_ecg/config.yaml` (copy from spec above)
- [ ] **T14** Implement Phase 21 in `scripts/analyse_mimic_iv_ecg.py`: upload the three ID CSVs + `split_summary.json` to HF Dataset
- [ ] **T15** Add Dataset Splits section to `scripts/report_template_mimic_iv_ecg.html` (T5u)
- [ ] **T16** Re-run script end-to-end; verify split counts sum to total filtered records; verify no patient overlap across splits
- [ ] **T11** Commit all outputs (excluding gitignored files) and push to `main` to deploy GitHub Pages and HuggingFace Space

---

## Notes & Decisions

- **Scale:** At 800K studies, loading all CSVs fits in RAM (record_list ≈ 68 MB, measurements ≈ 172 MB) but waveform scanning is expensive — use `sample_waveforms: 200` for header stats rather than reading all 800K .hea files
- **Derived intervals:** PR, QRS, QT are not stored directly; compute from `p_onset`, `qrs_onset`, `qrs_end`, `t_end` columns in the analysis script
- **report_0…report_17:** These columns are sparsely populated (most records have only a few phrases); flatten all non-null report fields into a single phrase counter
- **ecg_time dates are shifted** (MIMIC-IV uses date-shifted times, e.g. year 2180) — analyse relative temporal distributions (year offset from patient admission, hour-of-day, day-of-week) rather than treating years as real calendar years
- **machine_measurements_original.csv vs machine_measurements.csv:** The "original" file contains pre-processed raw values; the standard file is the cleaned version. Prefer the standard file for analysis; note discrepancies in the summary
- **waveform_note_links.csv covers only 609K of 800K records** — the missing ~191K have no linked clinical note; the note-link coverage section should highlight this gap
- **Lead completeness scan (Phase 15):** Reading 800K `.hea` files is I/O-bound, not CPU-bound — plain text parsing (or `wfdb.rdheader()`) is faster than loading full signals. Expect ~5–15 min on a spinning disk, ~1–3 min on SSD. Cap `incomplete_records` list at 500 entries in the JSON.
- **Signal quality scan (Phase 16):** Reading `.dat` binary signals is much slower than headers (~120 KB per file × 2000 = 240 MB of I/O). Default `sample_signal_quality: 2000` gives a statistically representative sample. Thresholds live under `signal_analysis:` in config — `flat_threshold` (mV) and `nan_count_threshold` (samples). Cap `flagged_records` list at 200 entries.
- **No explicit quality flags (Phase 17):** MIMIC-IV ECG has no PTB-XL-equivalent annotations (no `baseline_drift`, `static_noise`, `burst_noise`, `electrodes_problems` flags). The `clean_record_criteria` therefore has no `exclude_quality_flags` block — all quality filtering is purely signal-derived (flat leads, NaN samples) plus metadata nulls (`ecg_time`, `rr_interval`, `report_0`).
- **Clean records are estimates for signal criteria:** Phase 17 applies `require_all_12_leads` and `no_missing_metadata` exhaustively (from full .hea scan + full CSV), but `no_flat_leads` and `no_nan_in_leads` are extrapolated from the `sample_signal_quality` sample. Document this caveat in `clean_records_summary.json`.
- **Lead naming variations:** Some MIMIC-IV records may label leads differently (e.g., `AVR` vs `aVR`). Normalise to uppercase before matching against the expected 12-lead set.
- **Quoted DATA keys in Jinja2 template:** Always use `"{{ key }}": {{ blob }},` (not `{{ key }}:`) — learned from PTB-XL+ bug where the bare key `12sl_label_freq` (starts with digit) caused a JS parse error that silently broke all charts
- **D3 vendor:** Reuse `scripts/vendor/d3.min.js` — do not re-download
- **docs/index.html and README.md must be updated together** (per CLAUDE.md) to stay in sync
- **HuggingFace Space** is auto-deployed by `.github/workflows/deploy-to-hf.yml` on push to `main`
- **`clean_records.csv` → HF Dataset directly (no GitHub):** The file is gitignored (`analysis/*/clean_records.csv`). Phase 19 of the analysis script loads `HF_DATASET_TOKEN` from `.env` (via `python-dotenv`) and calls `huggingface_hub.HfApi.upload_file()` immediately after generating the CSV. No size limit on HF Dataset repos. `.env.example` documents the required keys; `.env` itself is gitignored.
- **`train/validate/test.csv` contain only `study_id` (record IDs, no metadata):** Users join against `record_list.csv` or `machine_measurements.csv` on `study_id` to retrieve paths, timestamps, or measurements for their own pipeline. This keeps the split files tiny (<10 MB each) and avoids duplicating 800K rows of metadata.
- **Patient-level splitting (Phase 18b):** All studies belonging to one `subject_id` are assigned to the same split. This prevents data leakage where the same patient appears in both train and test sets. The split is done on the unique patient list (stratified if `stratify_by` is set), then the study list is mapped back. With 160K patients and an 80/10/10 split, expect ~128K/16K/16K patients per split and proportional study counts.
- **Stratification:** When `stratify_by` is a continuous column (e.g. `qrs_axis`), the column is binned into `stratify_bins` equal-width bins before applying scikit-learn's `StratifiedShuffleSplit` at the patient level (using the modal bin per patient). If `stratify_by: null`, use plain random shuffle. Falls back to unstratified if any bin has too few patients for the split ratio.
- **Filter application order (Phase 18b):** (1) start from `clean_records.csv`, (2) left-join `machine_measurements.csv` for numeric filter columns, (3) apply year / RR / QRS-axis bounds, (4) apply phrase include/exclude, (5) apply `max_studies_per_patient` cap (random sample per patient, seeded), (6) split patients, (7) map studies back, (8) write CSVs (study_id only).
