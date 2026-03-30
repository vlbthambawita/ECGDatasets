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
    └── config.yaml

scripts/
├── analyse_mimic_iv_ecg.py
└── report_template_mimic_iv_ecg.html

docs/
└── analysis/
    └── mimic_iv_ecg/
        ├── data/
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
        │   └── signal_quality.json
        └── report.html
```

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
  report_dir:  docs/analysis/mimic_iv_ecg
  data_dir:    docs/analysis/mimic_iv_ecg/data
  report_html: docs/analysis/mimic_iv_ecg/report.html

analysis:
  top_n_reports:     40        # top N machine-report phrases to include in frequency chart
  top_n_carts:       30        # top N ECG cart IDs
  max_records:       null      # null = all; set integer (e.g. 5000) for fast test runs
  sample_waveforms:  200       # number of .hea files to read for waveform header stats
  sample_signal_quality: 2000  # number of .dat files to read for flat/missing lead detection
  missing_threshold_pct: 5.0   # flag measurements with >N% missing values
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

#### Phase 16 — Signal Quality: Flat & Missing Lead Detection (sampled)
Read `sample_signal_quality` randomly selected `.dat` files (via `wfdb.rdsamp()`) and for each record inspect every lead signal:

**Flat-line detection:** a lead is considered flat if `np.std(signal) < flat_std_threshold` (default 0.01 mV equivalent after ADC scaling).

**Near-zero / dropout detection:** a lead is considered dropped out if more than `dropout_zero_pct`% of samples are exactly 0 (after baseline subtraction).

**Clipping detection:** a lead is clipped if more than `clip_pct`% of samples equal the ADC min or max value (−32768 or +32767 for 16-bit).

Add these thresholds to `config.yaml`:
```yaml
  flat_std_threshold:  0.01    # mV — std below this = flat lead
  dropout_zero_pct:    50.0    # % — fraction of zero samples = dropout
  clip_pct:            1.0     # % — fraction of clipped samples = clipping
```

Per record, flag any leads that are flat, dropped-out, or clipped.

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

#### Phase 17 — Generate HTML Report (D3.js)
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
| Signal quality — flat/dropout/clip per lead | Grouped bar (tabbed: flat / dropout / clip) | `signal_quality.json` |

- Each chart: tooltip on hover, "Download SVG" button, stats table below with "Download CSV" button
- Sections (sidebar nav): Summary → Record Coverage → Temporal → Studies per Patient → Measurements → Report Phrases → Carts & Equipment → Note Links → Waveform Headers → Lead Completeness → Signal Quality
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
wfdb>=4.1          # reading .hea headers and .dat waveforms
pandas>=2.0
numpy>=1.24
pyyaml>=6.0
tqdm>=4.65
jinja2>=3.1        # HTML report templating
```

### Front-end (bundled into report.html)
```
d3 v7     # vendored at scripts/vendor/d3.min.js — no CDN dependency
```

---

## Tasks (in order)

- [ ] **T1** Create output directories: `analysis/mimic_iv_ecg/`, `docs/analysis/mimic_iv_ecg/`, `docs/analysis/mimic_iv_ecg/data/`
- [ ] **T2** Write `analysis/mimic_iv_ecg/config.yaml` with all parameters above
- [ ] **T3** Confirm `scripts/vendor/d3.min.js` exists (reuse from PTB-XL pipeline)
- [ ] **T4** Write `scripts/analyse_mimic_iv_ecg.py`:
  - [ ] T4a — CLI entry point + config loader + path validation
  - [ ] T4b — Data loaders: record_list, measurements, note_links CSVs; parse ecg_time as datetime
  - [ ] T4c — Dataset summary → `data/dataset_summary.json`
  - [ ] T4d — Record coverage analysis → `data/record_coverage.json`
  - [ ] T4e — Temporal distribution (year / month / hour / dow) → `data/temporal_distribution.json`
  - [ ] T4f — Studies-per-patient distribution → `data/studies_per_patient.json`
  - [ ] T4g — Measurement summary statistics → `data/measurement_stats.json`
  - [ ] T4h — Missing value analysis → `data/measurement_missing.json`
  - [ ] T4i — Interval distributions (RR, PR, QRS, QT) → `data/interval_distributions.json`
  - [ ] T4j — Axis distributions (p_axis, qrs_axis, t_axis) → `data/axis_distributions.json`
  - [ ] T4k — Machine report text frequency (top-N phrases) → `data/report_text_freq.json`
  - [ ] T4l — ECG cart usage → `data/cart_usage.json`
  - [ ] T4m — Bandwidth & filter profiles → `data/bandwidth_filtering.json`
  - [ ] T4n — Waveform–note link coverage → `data/note_link_coverage.json`
  - [ ] T4o — Waveform header stats (sampled .hea reads) → `data/waveform_header_stats.json`
  - [ ] T4p — Lead completeness (full .hea scan, all records) → `data/lead_completeness.json`
  - [ ] T4q — Signal quality: flat/dropout/clip detection (sampled .dat reads) → `data/signal_quality.json`
  - [ ] T4r — HTML report generator: render `scripts/report_template_mimic_iv_ecg.html` via Jinja2
- [ ] **T5** Write `scripts/report_template_mimic_iv_ecg.html` (Jinja2 + D3 template):
  - [ ] T5a — Sidebar nav + responsive layout (reuse PTB-XL/PTB-XL+ template structure)
  - [ ] T5b — Summary stat cards
  - [ ] T5c — Record coverage grouped bar chart
  - [ ] T5d — Temporal distribution charts (by year, by hour-of-day)
  - [ ] T5e — Studies-per-patient histogram
  - [ ] T5f — Measurement missing values horizontal bar
  - [ ] T5g — Measurement stats table
  - [ ] T5h — Interval distributions histograms (tabbed: RR / PR / QRS / QT)
  - [ ] T5i — Axis distributions bar histograms (P / QRS / T axes, tabbed)
  - [ ] T5j — Machine report phrase frequency horizontal bar
  - [ ] T5k — Cart usage bar chart
  - [ ] T5l — Bandwidth & filter donut charts
  - [ ] T5m — Note link coverage cards + bar
  - [ ] T5n — Waveform header stats cards + table
  - [ ] T5o — Lead completeness horizontal bar (per-lead absence rate) + table of incomplete records
  - [ ] T5p — Signal quality grouped bar charts (tabbed: flat / dropout / clipped) + flagged records table
  - [ ] T5q — Shared `downloadSVG()` utility + per-chart download button
  - [ ] T5r — Shared `downloadTableCSV()` utility + per-table download button
  - [ ] T5s — **Ensure all DATA keys are quoted strings in the Jinja2 template** (`"{{ key }}": {{ blob }},`) to avoid JS syntax errors from numeric-prefixed keys
- [ ] **T6** Run the script end-to-end (first with `max_records: 5000` for a fast test, then `null` for full run)
- [ ] **T7** Open `docs/analysis/mimic_iv_ecg/report.html` in a browser; verify all D3 charts render
- [ ] **T8** Update `docs/index.html` — add MIMIC-IV ECG row with "View Report" link
- [ ] **T9** Update `README.md` to list MIMIC-IV ECG as an available dataset
- [ ] **T10** Commit all outputs and push to `main` to deploy to GitHub Pages and HuggingFace Space

---

## Notes & Decisions

- **Scale:** At 800K studies, loading all CSVs fits in RAM (record_list ≈ 68 MB, measurements ≈ 172 MB) but waveform scanning is expensive — use `sample_waveforms: 200` for header stats rather than reading all 800K .hea files
- **Derived intervals:** PR, QRS, QT are not stored directly; compute from `p_onset`, `qrs_onset`, `qrs_end`, `t_end` columns in the analysis script
- **report_0…report_17:** These columns are sparsely populated (most records have only a few phrases); flatten all non-null report fields into a single phrase counter
- **ecg_time dates are shifted** (MIMIC-IV uses date-shifted times, e.g. year 2180) — analyse relative temporal distributions (year offset from patient admission, hour-of-day, day-of-week) rather than treating years as real calendar years
- **machine_measurements_original.csv vs machine_measurements.csv:** The "original" file contains pre-processed raw values; the standard file is the cleaned version. Prefer the standard file for analysis; note discrepancies in the summary
- **waveform_note_links.csv covers only 609K of 800K records** — the missing ~191K have no linked clinical note; the note-link coverage section should highlight this gap
- **Lead completeness scan (Phase 15):** Reading 800K `.hea` files is I/O-bound, not CPU-bound — plain text parsing (or `wfdb.rdheader()`) is faster than loading full signals. Expect ~5–15 min on a spinning disk, ~1–3 min on SSD. Cap `incomplete_records` list at 500 entries in the JSON.
- **Signal quality scan (Phase 16):** Reading `.dat` binary signals is much slower than headers (~120 KB per file × 2000 = 240 MB of I/O). Default `sample_signal_quality: 2000` gives a statistically representative sample. The flat/dropout/clip thresholds are in `config.yaml` and tunable. Cap `flagged_records` list at 200 entries.
- **Lead naming variations:** Some MIMIC-IV records may label leads differently (e.g., `AVR` vs `aVR`). Normalise to uppercase before matching against the expected 12-lead set.
- **Quoted DATA keys in Jinja2 template:** Always use `"{{ key }}": {{ blob }},` (not `{{ key }}:`) — learned from PTB-XL+ bug where the bare key `12sl_label_freq` (starts with digit) caused a JS parse error that silently broke all charts
- **D3 vendor:** Reuse `scripts/vendor/d3.min.js` — do not re-download
- **docs/index.html and README.md must be updated together** (per CLAUDE.md) to stay in sync
- **HuggingFace Space** is auto-deployed by `.github/workflows/deploy-to-hf.yml` on push to `main`
