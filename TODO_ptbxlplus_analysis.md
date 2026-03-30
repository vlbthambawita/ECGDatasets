# PTB-XL+ Dataset Analysis — Implementation Plan

## Goal

Build a configurable Python analysis script for the PTB-XL+ ECG dataset that produces:
1. A visual interactive HTML report (D3.js charts) saved in `docs/analysis/ptbxlplus/report.html`
2. JSON data files in `docs/analysis/ptbxlplus/data/` consumed by the D3 charts
3. Update `docs/index.html` to replace the "Coming soon" placeholder with a "View Report" link for PTB-XL+

---

## Dataset Facts (from exploration)

- **Location:** `/work/vajira/DATA/ptbxl_plus/physionet.org/files/ptb-xl-plus/1.0.1/`
- **Records:** 21,799 (same ECG IDs as PTB-XL; this dataset adds derived features)
- **RECORDS file:** `RECORDS` — one record path per line
- **Subdirectories:**

```
1.0.1/
├── features/
│   ├── 12sl_features.csv          # 21,799 rows × ~196 columns — 12SL algorithm features
│   ├── ecgdeli_features.csv        # 21,799 rows × ~196 columns — ECGDeli algorithm features
│   ├── unig_features.csv           # 21,795 rows × ~196 columns — UNIG algorithm features
│   └── feature_description.csv    # 196 rows — maps feature names to clinical description + LOINC + units
├── labels/
│   ├── ptbxl_statements.csv        # 21,799 rows — PTB-XL SCP codes with SNOMED expansions
│   ├── 12sl_statements.csv         # 21,799 rows — 12SL algorithm statements with SNOMED expansions
│   ├── snomed_description.csv      # 287 rows — SNOMED concept descriptions
│   └── mapping/
│       ├── 12slv23ToSNOMED.csv     # 12SL label → SNOMED mapping
│       ├── ptbxlToSNOMED.csv       # PTB-XL SCP code → SNOMED mapping
│       └── apply_snomed_mapping.py # reference script for applying mappings
├── fiducial_points/
│   └── ecgdeli/                   # per-record .atr files (ECGDeli delineation)
│       └── NNNNN/
│           ├── NNNNN_points_global.atr
│           ├── NNNNN_points_lead_I.atr
│           ├── NNNNN_points_lead_II.atr
│           └── ... (one per lead: I, II, III, V1–V6, aVR, aVL, aVF)
└── median_beats/
    ├── 12sl/                      # 12SL median beat waveforms
    │   └── NNNNN/
    │       ├── NNNNN_medians.dat
    │       └── NNNNN_medians.hea
    └── unig/                      # UNIG median beat waveforms
        └── NNNNN/
            ├── NNNNN_medians.dat
            └── NNNNN_medians.hea
```

- **Leads (12):** I, II, III, aVR, aVL, aVF, V1–V6
- **Feature sources:** 12SL (12-lead algorithm), ECGDeli (open-source delineator), UNIG (University of Glasgow algorithm)
- **Label sources:** PTB-XL SCP codes (cardiologist annotations) + 12SL algorithm statements
- **SNOMED mappings:** both label sets are expanded to SNOMED CT concepts

---

## Deliverables

```
analysis/
└── ptbxlplus/
    └── config.yaml

docs/
└── analysis/
    └── ptbxlplus/
        ├── data/                          ← JSON files consumed by D3 charts
        │   ├── dataset_summary.json
        │   ├── record_coverage.json
        │   ├── feature_missing_12sl.json
        │   ├── feature_missing_ecgdeli.json
        │   ├── feature_missing_unig.json
        │   ├── feature_stats_12sl.json
        │   ├── feature_stats_ecgdeli.json
        │   ├── feature_stats_unig.json
        │   ├── ptbxl_label_freq.json
        │   ├── 12sl_label_freq.json
        │   ├── label_cooccurrence.json
        │   ├── snomed_coverage.json
        │   ├── fiducial_coverage.json
        │   ├── median_beat_coverage.json
        │   └── cross_source_agreement.json
        └── report.html                   ← self-contained D3 report
```

---

## Configuration File

`analysis/ptbxlplus/config.yaml` — controls all runtime parameters:

```yaml
dataset:
  root: /work/vajira/DATA/ptbxl_plus/physionet.org/files/ptb-xl-plus/1.0.1
  records_file: RECORDS

  features:
    12sl: features/12sl_features.csv
    ecgdeli: features/ecgdeli_features.csv
    unig: features/unig_features.csv
    description: features/feature_description.csv

  labels:
    ptbxl: labels/ptbxl_statements.csv
    12sl: labels/12sl_statements.csv
    snomed: labels/snomed_description.csv
    mapping_ptbxl: labels/mapping/ptbxlToSNOMED.csv
    mapping_12sl: labels/mapping/12slv23ToSNOMED.csv

  fiducial_points:
    ecgdeli: fiducial_points/ecgdeli

  median_beats:
    12sl: median_beats/12sl
    unig: median_beats/unig

output:
  report_dir: docs/analysis/ptbxlplus
  data_dir: docs/analysis/ptbxlplus/data
  report_html: docs/analysis/ptbxlplus/report.html

analysis:
  top_n_labels: 30              # top N labels to include in frequency charts
  cooccurrence_top_n: 25        # top N labels for co-occurrence heatmap
  missing_threshold_pct: 5.0    # flag features with >N% missing values
  max_records: null             # null = all; set integer for fast test runs
  sample_size_heatmap: 2000     # records sampled for per-record heatmaps
```

---

## Script Structure

**File:** `scripts/analyse_ptbxlplus.py`

### Phases

#### Phase 1 — Load & Validate Config
- Parse `config.yaml` (path passed as CLI arg: `--config`)
- Resolve all paths relative to repo root or as absolute
- Validate that all expected files/directories exist; warn on missing

#### Phase 2 — Load Data
- Load all three feature CSVs into DataFrames; note row counts
- Load `feature_description.csv` to build `feature_id → {description, unit, loinc}` lookup
- Load `ptbxl_statements.csv` and `12sl_statements.csv`; parse SCP code columns from string-repr to Python objects
- Load `snomed_description.csv` and both mapping CSVs
- Scan `fiducial_points/ecgdeli/` and `median_beats/{12sl,unig}/` to enumerate present record IDs

#### Phase 3 — Dataset Summary
Compute and serialize to `data/dataset_summary.json`:
- Total record count per source (12SL, ECGDeli, UNIG features; PTB-XL labels; 12SL labels; fiducial points; median beats)
- Number of features per source
- Number of unique SNOMED concepts covered
- File size summary

#### Phase 4 — Record Coverage Analysis
Identify which records appear in each of the five data sources (12SL features, ECGDeli features, UNIG features, PTB-XL labels, 12SL labels, ECGDeli fiducial points, 12SL median beats, UNIG median beats).

Serialize to `data/record_coverage.json`:
- Per-source record count
- Missing record IDs vs. the canonical `RECORDS` file
- Venn-style intersection counts (records present in all sources vs. missing from ≥1 source)

#### Phase 5 — Feature Analysis (three sources)
For each feature CSV (12SL, ECGDeli, UNIG):

**5a — Missing values**
- Compute per-feature missing % across all records
- Flag features above `missing_threshold_pct`
- Serialize to `data/feature_missing_{source}.json`:
  - List of `{feature_id, description, unit, missing_pct}` sorted descending

**5b — Summary statistics**
- For a representative set of features (P/QRS/T amplitudes, durations, PQ/QRS/QT intervals), compute mean, std, min, p25, p50, p75, max across all records and all leads
- Serialize to `data/feature_stats_{source}.json`:
  - List of `{feature_id, description, unit, mean, std, p25, p50, p75, min, max}` (one row per feature × lead aggregated)

#### Phase 6 — Label Analysis

**6a — PTB-XL label frequency**
- Parse `scp_codes` column; count occurrences of each SCP code
- Serialize top-N to `data/ptbxl_label_freq.json`:
  - `{code, snomed_id, description, count, pct}`

**6b — 12SL label frequency**
- Parse `statements` column; count occurrences of each statement code
- Serialize top-N to `data/12sl_label_freq.json`:
  - `{code, snomed_id, description, count, pct}`

**6c — Label co-occurrence**
- Build a binary label matrix (records × top-N labels) for each label source
- Compute pairwise co-occurrence counts
- Serialize to `data/label_cooccurrence.json`:
  - `{source, labels: [...], matrix: [[...]]}`

**6d — SNOMED coverage**
- For both label sets, count how many unique SNOMED concepts appear, and what fraction of `snomed_description.csv` is covered
- Serialize to `data/snomed_coverage.json`

#### Phase 7 — Fiducial Point Coverage
Scan `fiducial_points/ecgdeli/` directory:
- Count records with global vs. per-lead .atr files
- For each lead, count records that have a per-lead .atr file
- Identify records in `RECORDS` but missing fiducial files
- Read a sample .atr file to verify format (using `wfdb.rdann`)
- Serialize to `data/fiducial_coverage.json`:
  - `{total_with_global, per_lead_counts: {lead: count}, missing_records: [...]}`

#### Phase 8 — Median Beat Coverage
Scan `median_beats/{12sl,unig}/` directories:
- For each source, count records with .dat/.hea pairs
- Read a sample .hea file to extract: leads, sampling rate, signal length, units
- Identify records in `RECORDS` but missing median beat files
- Serialize to `data/median_beat_coverage.json`:
  - Per-source: `{record_count, leads, sampling_rate, duration_ms, missing_records: [...]}`

#### Phase 9 — Cross-Source Agreement
Compare PTB-XL cardiologist labels vs. 12SL algorithm statements for the same records via their shared SNOMED expansions:
- For each record, compute: agreement (both flagged), PTB-XL only, 12SL only
- Summarize agreement rate per SNOMED concept
- Serialize to `data/cross_source_agreement.json`

#### Phase 10 — Generate HTML Report (D3.js)
Produce a **self-contained** `report.html` (rendered from `scripts/report_template_ptbxlplus.html` via Jinja2) that:
- Bundles D3 v7 inline from `scripts/vendor/d3.min.js` (no CDN)
- Inlines all JSON data blobs as JS variables
- Renders all charts client-side using D3:

| Chart | Type | Data source |
|-------|------|-------------|
| Dataset summary cards | Stat cards | `dataset_summary.json` |
| Record coverage per source | Grouped bar | `record_coverage.json` |
| Feature missing % (12SL) | Horizontal bar | `feature_missing_12sl.json` |
| Feature missing % (ECGDeli) | Horizontal bar | `feature_missing_ecgdeli.json` |
| Feature missing % (UNIG) | Horizontal bar | `feature_missing_unig.json` |
| Feature stats — key intervals | Box plot / violin | `feature_stats_{source}.json` |
| PTB-XL label frequency | Bar chart | `ptbxl_label_freq.json` |
| 12SL label frequency | Bar chart | `12sl_label_freq.json` |
| Label co-occurrence | Heatmap | `label_cooccurrence.json` |
| SNOMED coverage | Donut chart | `snomed_coverage.json` |
| Fiducial point coverage per lead | Bar chart | `fiducial_coverage.json` |
| Median beat coverage | Bar chart | `median_beat_coverage.json` |
| Cross-source label agreement | Diverging bar | `cross_source_agreement.json` |

- Each chart: tooltip on hover, "Download SVG" button, stats table below with "Download CSV" button
- Sections (sidebar nav): Summary → Record Coverage → Feature Analysis → Label Analysis → SNOMED & Mappings → Fiducial Points → Median Beats → Cross-Source Agreement
- Responsive layout, sticky sidebar nav for section jumping

---

## Update `docs/index.html`

Replace the PTB-XL+ "Coming soon" cell with a "View Report" link (matching the PTB-XL row style):

```diff
-        <td><span class="analysis-soon">&#128337; Coming soon</span></td>
+        <td><a class="analysis-link" href="analysis/ptbxlplus/report.html" target="_blank">&#128202; View Report</a></td>
```

---

## Dependencies

### Python
```
wfdb>=4.1          # reading .atr fiducial annotation files and .hea/.dat median beats
pandas>=2.0
numpy>=1.24
pyyaml>=6.0
tqdm>=4.65
jinja2>=3.1        # HTML report templating
```

> matplotlib/seaborn are **not** required — all visualizations are D3.js in the browser.

### Front-end (bundled into report.html)
```
d3 v7     # vendored at scripts/vendor/d3.min.js — no CDN dependency
```

---

## Tasks (in order)

- [ ] **T1** Create output directories: `analysis/ptbxlplus/`, `docs/analysis/ptbxlplus/`, `docs/analysis/ptbxlplus/data/`
- [ ] **T2** Write `analysis/ptbxlplus/config.yaml` with all parameters above
- [ ] **T3** Vendor D3: confirm `scripts/vendor/d3.min.js` exists (reuse from PTB-XL pipeline)
- [ ] **T4** Write `scripts/analyse_ptbxlplus.py`:
  - [ ] T4a — CLI entry point + config loader + path validation
  - [ ] T4b — Data loaders: features CSVs, labels CSVs, SNOMED/mapping CSVs
  - [ ] T4c — Dataset summary → `data/dataset_summary.json`
  - [ ] T4d — Record coverage analysis → `data/record_coverage.json`
  - [ ] T4e — Feature missing values (all 3 sources) → `data/feature_missing_{source}.json`
  - [ ] T4f — Feature summary stats (key intervals/amplitudes) → `data/feature_stats_{source}.json`
  - [ ] T4g — Label frequency: PTB-XL + 12SL → `data/ptbxl_label_freq.json`, `data/12sl_label_freq.json`
  - [ ] T4h — Label co-occurrence matrix → `data/label_cooccurrence.json`
  - [ ] T4i — SNOMED coverage → `data/snomed_coverage.json`
  - [ ] T4j — Fiducial point coverage (scan .atr files) → `data/fiducial_coverage.json`
  - [ ] T4k — Median beat coverage (scan .hea/.dat files) → `data/median_beat_coverage.json`
  - [ ] T4l — Cross-source label agreement → `data/cross_source_agreement.json`
  - [ ] T4m — HTML report generator: render `scripts/report_template_ptbxlplus.html` via Jinja2
- [ ] **T5** Write `scripts/report_template_ptbxlplus.html` (Jinja2 + D3 template):
  - [ ] T5a — Sidebar nav + responsive layout (reuse PTB-XL template structure)
  - [ ] T5b — Summary stat cards
  - [ ] T5c — Record coverage grouped bar chart
  - [ ] T5d — Feature missing % horizontal bar charts (tabbed: 12SL / ECGDeli / UNIG)
  - [ ] T5e — Feature stats box/violin plots for key intervals
  - [ ] T5f — Label frequency bar charts (tabbed: PTB-XL / 12SL)
  - [ ] T5g — Label co-occurrence heatmap
  - [ ] T5h — SNOMED coverage donut chart
  - [ ] T5i — Fiducial + median beat coverage bar charts
  - [ ] T5j — Cross-source agreement diverging bar chart
  - [ ] T5k — Shared `downloadSVG()` utility + per-chart download button
  - [ ] T5l — Shared `downloadTableCSV()` utility + per-table download button
- [ ] **T6** Run the script end-to-end and verify all JSON files are written
- [ ] **T7** Open `docs/analysis/ptbxlplus/report.html` in a browser; verify all D3 charts render
- [ ] **T8** Update `docs/index.html` — replace PTB-XL+ "Coming soon" with "View Report" link
- [ ] **T9** Update `README.md` if it lists available reports
- [ ] **T10** Commit all outputs (`docs/analysis/ptbxlplus/`, updated `docs/index.html`) and push to `main` to trigger deployment to GitHub Pages and the HuggingFace Space

---

## Notes & Decisions

- PTB-XL+ shares its ECG IDs with PTB-XL (same 21,799 records); the analysis does **not** re-load raw waveforms — it analyses derived features, labels, fiducial annotations, and median beats only
- UNIG features have 4 fewer rows (21,795 vs 21,799) — the coverage analysis will identify which record IDs are missing
- The "Coming soon" span class is `analysis-soon`; the replacement should use the existing `analysis-link` class so it inherits the correct styling
- Both `docs/index.html` and `README.md` must be updated together to stay in sync (per CLAUDE.md)
- The HuggingFace Space mirror is auto-deployed by `.github/workflows/deploy-to-hf.yml` on push to `main` — no manual step needed
- Reuse `scripts/vendor/d3.min.js` already vendored for the PTB-XL pipeline — do not re-download
- `wfdb.rdann()` is used to read `.atr` fiducial annotation files; `wfdb.rdsamp()` is used to peek at `.hea` headers for median beats
- For the cross-source agreement chart, map both label sets to their shared SNOMED IDs first (via the mapping CSVs), then compare at the SNOMED level — raw code strings are not directly comparable
- `max_records: null` runs on all records; set to a small integer (e.g., 200) for fast iteration during development
