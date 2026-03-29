# PTB-XL Dataset Analysis — Implementation Plan

## Goal

Build a configurable Python analysis script for the PTB-XL ECG dataset that produces:
1. A visual interactive HTML report (D3.js charts) saved in `analysis/ptbxl/report.html`
2. JSON data files in `analysis/ptbxl/data/` consumed by the D3 charts
3. A `clean_records.csv` listing ECG IDs and fold numbers for fully clean records

---

## Dataset Facts (from exploration)

- **Location:** `/work/vajira/DATA/EXG_PTB_XL/physionet/files/ptb-xl/1_0_1/`
- **Records:** 21,837 unique 12-lead ECG recordings
- **Metadata:** `ptbxl_database.csv` (28 columns)
- **Signal resolutions:** 100 Hz (`records100/`) and 500 Hz (`records500/`)
- **Leads (12):** I, II, III, AVR, AVL, AVF, V1–V6
- **Folds:** `strat_fold` column, values 1–10 (stratified cross-validation splits)
- **Diagnostic codes:** `scp_codes` column (dict of SCP-ECG codes + confidence)
- **Quality flags:** `baseline_drift`, `static_noise`, `burst_noise`, `electrodes_problems`, `extra_beats`

---

## Deliverables

```
analysis/
└── ptbxl/
    ├── data/                        ← JSON data files consumed by D3 charts
    │   ├── metadata_summary.json
    │   ├── age_distribution.json
    │   ├── sex_distribution.json
    │   ├── height_weight.json
    │   ├── recording_site.json
    │   ├── strat_fold.json
    │   ├── scp_top_codes.json
    │   ├── diagnostic_class.json
    │   ├── heart_axis.json
    │   ├── quality_flags.json
    │   ├── missing_metadata.json
    │   ├── missing_ecg_leads.json
    │   ├── flat_signal_leads.json
    │   └── clean_records_per_fold.json
    ├── report.html          ← self-contained report (D3 charts inline, no CDN)
    └── clean_records.csv    ← ecg_id, strat_fold for fully clean records
```

---

## Configuration File

`analysis/ptbxl/config.yaml` — controls all runtime parameters:

```yaml
dataset:
  root: /work/vajira/DATA/EXG_PTB_XL/physionet/files/ptb-xl/1_0_1
  metadata_file: ptbxl_database.csv
  scp_file: scp_statements.csv
  signal_resolution: 100          # 100 or 500 Hz
  max_records: null               # null = all; set integer for quick test runs

output:
  report_dir: analysis/ptbxl
  data_dir: analysis/ptbxl/data
  clean_csv: analysis/ptbxl/clean_records.csv
  report_html: analysis/ptbxl/report.html

signal_analysis:
  flat_threshold: 0.01            # mV; leads with std below this are "flat"
  nan_count_threshold: 1          # samples with >= this many NaN values are flagged
  check_500hz: false              # whether to also check 500 Hz signals

clean_record_criteria:
  require_all_12_leads: true
  no_flat_leads: true
  no_nan_in_leads: true
  no_missing_metadata:            # list of required non-null metadata columns
    - age
    - sex
    - height
    - weight
    - recording_date
    - report
    - scp_codes
    - strat_fold
  exclude_quality_flags:          # records with any of these set are excluded
    - baseline_drift
    - static_noise
    - burst_noise
    - electrodes_problems

metadata_analysis:
  top_n_scp_codes: 20             # number of top SCP codes to include in chart
  top_n_sites: 10
  missing_heatmap_sample_size: 2000  # number of records sampled for heatmaps
```

---

## Script Structure

**File:** `scripts/analyse_ptbxl.py`

### Phases

#### Phase 1 — Load & Validate Config
- Parse `config.yaml` (path passed as CLI arg: `--config`)
- Resolve all paths relative to repo root or as absolute

#### Phase 2 — Load Metadata
- Load `ptbxl_database.csv` into a DataFrame
- Load `scp_statements.csv` for code-to-label mapping
- Parse `scp_codes` column from string-dict to actual dict
- Parse quality-flag columns to boolean

#### Phase 3 — Metadata Analysis
Compute statistics and serialize to JSON (rendered as interactive D3 charts in Phase 8):

| # | Analysis | JSON output |
|---|----------|-------------|
| 1 | Record count summary | `data/metadata_summary.json` |
| 2 | Age distribution | `data/age_distribution.json` |
| 3 | Sex distribution | `data/sex_distribution.json` |
| 4 | Height & weight | `data/height_weight.json` |
| 5 | Recording site distribution | `data/recording_site.json` |
| 6 | Strat fold distribution | `data/strat_fold.json` |
| 7 | Top-N SCP diagnostic codes | `data/scp_top_codes.json` |
| 8 | Diagnostic class distribution | `data/diagnostic_class.json` |
| 9 | Heart axis category counts | `data/heart_axis.json` |
| 10 | Quality flag counts | `data/quality_flags.json` |

#### Phase 4 — Missing Metadata Analysis
- Compute null/NaN counts per column
- Flag columns with any missing values
- Serialize to JSON:
  - `data/missing_metadata.json` — per-column % missing (for bar chart) + sampled binary presence matrix (for heatmap)

#### Phase 5 — ECG Signal Analysis (missing & flat leads)
For each record (up to `max_records`):
- Load signal via `wfdb.rdsamp()`
- For each of 12 leads:
  - Count NaN samples → flag as "missing values" if ≥ threshold
  - Compute std → flag as "flat" if < `flat_threshold`
  - Flag if lead is entirely zero

Aggregate and serialize to JSON:
- `data/missing_ecg_leads.json` — % of records with ≥ 1 missing value per lead + sampled per-record presence matrix
- `data/flat_signal_leads.json` — % of records with flat signal per lead

#### Phase 6 — Clean Record Identification
Apply all criteria from `clean_record_criteria`:
1. All 12 leads present and loadable
2. No NaN values in any lead (above threshold)
3. No flat leads
4. No missing values in required metadata columns
5. No quality flags set (from `exclude_quality_flags`)

Output: `clean_records.csv`

```
ecg_id,strat_fold
1,9
5,3
...
```

Also serialize: clean vs. dirty record count per fold → `data/clean_records_per_fold.json`

#### Phase 7 — Export JSON Data Files
All JSON files are written to `analysis/ptbxl/data/` as the analysis phases complete (Phases 3–6 each write their own files). No separate export phase is needed — JSON writing is integral to each phase.

#### Phase 8 — Generate HTML Report (D3.js)
Produce a **self-contained** `report.html` that:
- Bundles the D3 v7 library source inline (no CDN, works offline)
- Reads the JSON data files via `fetch()` — or optionally inlines them as JS variables for fully standalone mode
- Renders all charts client-side using D3:
  - **Histogram** — age distribution (brushable x-axis)
  - **Bar charts** — sex, fold, diagnostic class, heart axis, SCP top codes, quality flags, missing metadata %, missing leads %, flat leads %, clean vs dirty per fold
  - **Scatter plot** — height vs weight (zoomable, with tooltip)
  - **Heatmap** — missing metadata per record (sampled), missing leads per record (sampled)
  - **Grouped bar** — clean vs dirty record count per fold
- Each chart has a **"Download SVG"** button that serialises the chart's `<svg>` node to a string and triggers a browser file download (no server required); filename derived from chart title (e.g., `age_distribution.svg`)
- Sections: Summary → Metadata Analysis → Missing Metadata → ECG Signal Analysis → Clean Records
- Each section has an interactive D3 chart + a stats table below it; each table has a **"Download CSV"** button
- Dataset overview card at the top (total records, date range, leads, folds)
- Responsive layout with a sticky sidebar nav for section jumping

---

## Dependencies

### Python (analysis script)
```
wfdb>=4.1
pandas>=2.0
numpy>=1.24
scipy>=1.11
pyyaml>=6.0
tqdm>=4.65
jinja2>=3.1      # for HTML report templating
```

> matplotlib and seaborn are **not** required — all visualizations are handled by D3 in the browser.

### Front-end (bundled into report.html)
```
d3 v7          # bundled inline from d3.min.js — no CDN dependency
```

The build step downloads `d3.min.js` once (or uses a vendored copy at `scripts/vendor/d3.min.js`) and inlines it into `report.html` via Jinja2 so the report is fully self-contained.

---

## Tasks (in order)

- [ ] **T1** Create `analysis/ptbxl/data/` and `scripts/vendor/` directories
- [ ] **T2** Write `analysis/ptbxl/config.yaml` with all parameters
- [ ] **T3** Vendor D3: download `d3.min.js` v7 to `scripts/vendor/d3.min.js`
- [ ] **T4** Write `scripts/analyse_ptbxl.py`:
  - [ ] T4a — CLI entry point + config loader
  - [ ] T4b — Metadata loader + SCP code parser
  - [ ] T4c — Metadata analysis → JSON (Phase 3)
  - [ ] T4d — Missing metadata analysis → JSON (Phase 4)
  - [ ] T4e — ECG signal analysis → JSON (Phase 5) — use tqdm, respect `max_records`
  - [ ] T4f — Clean record identification + `clean_records.csv` (Phase 6)
  - [ ] T4g — HTML report generator: render `scripts/report_template.html` via Jinja2, inlining `d3.min.js` and all JSON blobs as JS variables (Phase 8)
- [ ] **T5** Write D3 chart modules inside `scripts/report_template.html` (Jinja2 template):
  - [ ] T5a — Histogram (age)
  - [ ] T5b — Bar charts (sex, fold, diagnostic class, heart axis, SCP codes, quality flags, missing metadata, missing leads, flat leads, clean per fold)
  - [ ] T5c — Scatter plot (height vs weight) with zoom + tooltip
  - [ ] T5d — Heatmaps (missing metadata, missing leads) with colour scale + tooltip
  - [ ] T5e — Shared `downloadSVG()` utility + per-chart "Download SVG" button
  - [ ] T5f — Shared `downloadTableCSV()` utility + per-table "Download CSV" button
  - [ ] T5g — Sidebar nav + responsive layout
- [ ] **T6** Run the script end-to-end and verify outputs
- [ ] **T7** Confirm `clean_records.csv` looks correct (spot check a few records)
- [ ] **T8** Open `report.html` in a browser and verify all D3 charts render correctly

---

## Notes & Decisions

- Signal loading uses the `wfdb` library (same as the official example script)
- **D3 v7** is used for all visualizations; charts are interactive (tooltips, zoom, brush) and render in any modern browser without a server
- Every chart exposes a **"Download SVG"** button implemented as a shared JS utility (`downloadSVG(svgNode, filename)`) that: (1) clones the SVG, (2) inlines computed CSS styles so the downloaded file renders correctly outside the browser, (3) prepends the XML declaration, and (4) triggers a `<a download>` click — no external library needed
- Every stats table exposes a **"Download CSV"** button implemented as a shared JS utility (`downloadTableCSV(tableEl, filename)`) that walks the `<thead>` and `<tbody>` rows, joins cells with commas, and triggers a `<a download>` click on the resulting Blob URL
- The report inlines both `d3.min.js` and all JSON data as JS variables → fully self-contained single HTML file, works offline
- matplotlib/seaborn are **not** used — removing them keeps the Python env lighter and the visualizations richer
- `max_records: null` runs on all 21,837 records; use a small integer (e.g., 500) for fast testing
- The signal analysis phase is the most time-consuming; a progress bar (tqdm) and optional `max_records` cap make it tractable during development
- `strat_fold` values in PTB-XL are 1–10; fold 0 does not exist — the script will assert this
- Quality flags in the raw CSV are stored as floats (NaN = not set, value = set); the script treats any non-NaN value as "flag present"
- The HTML/JS template lives in `scripts/report_template.html`; Jinja2 renders it with the inlined D3 source and JSON blobs to produce the final `report.html`
