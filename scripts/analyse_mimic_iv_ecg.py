#!/usr/bin/env python3
"""
MIMIC-IV ECG Dataset Analysis Script
Produces JSON data files and a self-contained D3.js HTML report.

Usage:
    python scripts/analyse_mimic_iv_ecg.py --config analysis/mimic_iv_ecg/config.yaml
"""
import argparse
import json
import random
import sys
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_LEADS = ["I", "II", "III", "aVR", "aVF", "aVL", "V1", "V2", "V3", "V4", "V5", "V6"]
LEAD_NORM = {l.upper(): l for l in EXPECTED_LEADS}
LEAD_NORM.update({"AVR": "aVR", "AVL": "aVL", "AVF": "aVF"})

NUMERIC_FIELDS = [
    ("rr_interval", "RR interval",   "ms"),
    ("p_onset",     "P-wave onset",  "ms"),
    ("p_end",       "P-wave end",    "ms"),
    ("qrs_onset",   "QRS onset",     "ms"),
    ("qrs_end",     "QRS end",       "ms"),
    ("t_end",       "T-wave end",    "ms"),
    ("p_axis",      "P-wave axis",   "degrees"),
    ("qrs_axis",    "QRS axis",      "degrees"),
    ("t_axis",      "T-wave axis",   "degrees"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


def compute_stats(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    n_total = len(series)
    if len(s) == 0:
        return {"count": 0, "missing_pct": 100.0,
                "mean": None, "std": None, "min": None,
                "p25": None, "p50": None, "p75": None, "max": None}
    return {
        "count":       int(len(s)),
        "missing_pct": round((n_total - len(s)) / n_total * 100, 2),
        "mean":        round(float(s.mean()), 3),
        "std":         round(float(s.std()), 3),
        "min":         round(float(s.min()), 3),
        "p25":         round(float(s.quantile(0.25)), 3),
        "p50":         round(float(s.median()), 3),
        "p75":         round(float(s.quantile(0.75)), 3),
        "max":         round(float(s.max()), 3),
    }


def histogram(series, n_bins=50, vmin=None, vmax=None):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return []
    lo = vmin if vmin is not None else float(s.min())
    hi = vmax if vmax is not None else float(s.max())
    if lo >= hi:
        return []
    bins = np.linspace(lo, hi, n_bins + 1)
    counts, edges = np.histogram(s, bins=bins)
    return [{"x0": round(float(edges[i]), 2), "x1": round(float(edges[i + 1]), 2),
             "count": int(counts[i])} for i in range(len(counts))]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Load Data
# ─────────────────────────────────────────────────────────────────────────────

def load_data(root, cfg, max_records):
    print("[Phase 2] Loading CSVs...")
    csv_cfg = cfg["dataset"]["csv"]

    records_df = pd.read_csv(root / csv_cfg["record_list"])
    if max_records:
        records_df = records_df.head(int(max_records))
    print(f"  record_list:  {len(records_df):,} rows")

    meas_df = pd.read_csv(root / csv_cfg["measurements"], low_memory=False)
    print(f"  measurements: {len(meas_df):,} rows × {meas_df.shape[1]} cols")

    dict_df = pd.read_csv(root / csv_cfg["data_dictionary"])

    links_df = pd.read_csv(root / csv_cfg["note_links"])
    print(f"  note_links:   {len(links_df):,} rows")

    for df in (records_df, meas_df, links_df):
        if "ecg_time" in df.columns:
            df["ecg_time"] = pd.to_datetime(df["ecg_time"], errors="coerce")

    return records_df, meas_df, dict_df, links_df


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Dataset Summary
# ─────────────────────────────────────────────────────────────────────────────

def dataset_summary(root, records_df, meas_df, links_df, out):
    print("[Phase 3] Dataset summary...")

    rec_studies  = set(records_df["study_id"])
    meas_studies = set(meas_df["study_id"])
    link_studies = set(links_df["study_id"])

    files_dir = root / "files"
    n_groups = len(list(files_dir.glob("p*"))) if files_dir.exists() else 0

    dt = records_df["ecg_time"].dropna() if "ecg_time" in records_df.columns else pd.Series(dtype="datetime64[ns]")

    result = {
        "total_records":               int(len(records_df)),
        "unique_patients":             int(records_df["subject_id"].nunique()),
        "unique_studies":              int(records_df["study_id"].nunique()),
        "records_with_measurements":   int(len(rec_studies & meas_studies)),
        "records_without_measurements":int(len(rec_studies - meas_studies)),
        "records_with_note_links":     int(len(rec_studies & link_studies)),
        "records_without_note_links":  int(len(rec_studies - link_studies)),
        "patient_group_folders":       n_groups,
        "ecg_time_range": {
            "min": str(dt.min()) if len(dt) else None,
            "max": str(dt.max()) if len(dt) else None,
        },
        "sampling_rate_hz": 500,
        "duration_s":       10,
        "leads":            12,
    }
    write_json(result, out / "dataset_summary.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — Record Coverage
# ─────────────────────────────────────────────────────────────────────────────

def record_coverage(records_df, meas_df, links_df, out):
    print("[Phase 4] Record coverage...")

    rec_ids  = set(records_df["study_id"])
    meas_ids = set(meas_df["study_id"])
    link_ids = set(links_df["study_id"])

    result = {
        "canonical_count": len(rec_ids),
        "sources": {
            "record_list":  {"count": len(rec_ids),
                             "missing_from_canonical": 0},
            "measurements": {"count": int(len(meas_ids & rec_ids)),
                             "missing_from_canonical": int(len(rec_ids - meas_ids))},
            "note_links":   {"count": int(len(link_ids & rec_ids)),
                             "missing_from_canonical": int(len(rec_ids - link_ids))},
        },
    }
    write_json(result, out / "record_coverage.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — Temporal Distribution
# ─────────────────────────────────────────────────────────────────────────────

def temporal_distribution(records_df, out):
    print("[Phase 5] Temporal distribution...")

    if "ecg_time" not in records_df.columns:
        return
    dt = records_df["ecg_time"].dropna()

    DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    MONTH = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    result = {
        "by_year":  [{"year":  int(k), "count": int(v)}
                     for k, v in dt.dt.year.value_counts().sort_index().items()],
        "by_month": [{"month": MONTH[int(k)-1], "month_num": int(k), "count": int(v)}
                     for k, v in dt.dt.month.value_counts().sort_index().items()],
        "by_hour":  [{"hour":  int(k), "count": int(v)}
                     for k, v in dt.dt.hour.value_counts().sort_index().items()],
        "by_dow":   [{"day":   DOW[int(k)], "count": int(v)}
                     for k, v in dt.dt.dayofweek.value_counts().sort_index().items()],
    }
    write_json(result, out / "temporal_distribution.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 6 — Studies per Patient
# ─────────────────────────────────────────────────────────────────────────────

def studies_per_patient(records_df, out):
    print("[Phase 6] Studies per patient...")

    counts = records_df.groupby("subject_id")["study_id"].count()
    stats = {
        "min":    int(counts.min()),
        "max":    int(counts.max()),
        "mean":   round(float(counts.mean()), 2),
        "median": float(counts.median()),
        "p25":    float(counts.quantile(0.25)),
        "p75":    float(counts.quantile(0.75)),
        "p95":    float(counts.quantile(0.95)),
    }

    buckets = [("1",    1,  1), ("2–5",  2,  5), ("6–10",  6, 10),
               ("11–20",11,20), ("21–50",21,50), ("51+",  51,99999)]
    hist = [{"bucket": lbl, "count": int(((counts >= lo) & (counts <= hi)).sum())}
            for lbl, lo, hi in buckets]

    write_json({"total_patients": int(len(counts)), "stats": stats, "histogram": hist},
               out / "studies_per_patient.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7 — Measurement Statistics
# ─────────────────────────────────────────────────────────────────────────────

def measurement_stats(meas_df, out):
    print("[Phase 7] Measurement statistics...")
    rows = []
    for field, description, unit in NUMERIC_FIELDS:
        if field not in meas_df.columns:
            continue
        s = compute_stats(meas_df[field])
        s.update({"field": field, "description": description, "unit": unit})
        rows.append(s)
    write_json({"fields": rows}, out / "measurement_stats.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8 — Missing Values
# ─────────────────────────────────────────────────────────────────────────────

def measurement_missing(meas_df, dict_df, threshold_pct, out):
    print("[Phase 8] Missing value analysis...")

    desc_map = {}
    if "Variable" in dict_df.columns and "Description" in dict_df.columns:
        for _, row in dict_df.iterrows():
            desc_map[str(row["Variable"]).strip()] = str(row["Description"]).strip()

    n = len(meas_df)
    rows = []
    for col in meas_df.columns:
        missing = int(meas_df[col].isna().sum())
        pct = round(missing / n * 100, 2) if n > 0 else 0.0
        rows.append({
            "field":         col,
            "description":   desc_map.get(col, ""),
            "missing_count": missing,
            "missing_pct":   pct,
            "flagged":       pct > threshold_pct,
        })
    rows.sort(key=lambda x: -x["missing_pct"])
    write_json({"total_records": n, "fields": rows}, out / "measurement_missing.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9 — Interval Distributions
# ─────────────────────────────────────────────────────────────────────────────

def interval_distributions(meas_df, out):
    print("[Phase 9] Interval distributions...")

    df = meas_df
    intervals = {}

    if "rr_interval" in df.columns:
        intervals["rr_interval"] = {
            "label": "RR Interval", "unit": "ms",
            "bins": histogram(df["rr_interval"], 60, 200, 2000),
        }

    if {"qrs_onset", "p_onset"} <= set(df.columns):
        pr = pd.to_numeric(df["qrs_onset"], errors="coerce") - pd.to_numeric(df["p_onset"], errors="coerce")
        intervals["pr_interval"] = {
            "label": "PR Interval", "unit": "ms",
            "bins": histogram(pr, 50, 50, 500),
        }

    if {"qrs_end", "qrs_onset"} <= set(df.columns):
        qrs = pd.to_numeric(df["qrs_end"], errors="coerce") - pd.to_numeric(df["qrs_onset"], errors="coerce")
        intervals["qrs_duration"] = {
            "label": "QRS Duration", "unit": "ms",
            "bins": histogram(qrs, 50, 40, 300),
        }

    if {"t_end", "qrs_onset"} <= set(df.columns):
        qt = pd.to_numeric(df["t_end"], errors="coerce") - pd.to_numeric(df["qrs_onset"], errors="coerce")
        intervals["qt_interval"] = {
            "label": "QT Interval", "unit": "ms",
            "bins": histogram(qt, 60, 200, 700),
        }

    write_json(intervals, out / "interval_distributions.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10 — Axis Distributions
# ─────────────────────────────────────────────────────────────────────────────

def axis_distributions(meas_df, out):
    print("[Phase 10] Axis distributions...")

    axes = {}
    for field, label in [("p_axis", "P-wave Axis"), ("qrs_axis", "QRS Axis"), ("t_axis", "T-wave Axis")]:
        if field not in meas_df.columns:
            continue
        axes[field] = {
            "label": label, "unit": "degrees",
            "bins": histogram(meas_df[field], 36, -180, 180),
        }
    write_json(axes, out / "axis_distributions.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 11 — Report Text Frequency
# ─────────────────────────────────────────────────────────────────────────────

def report_text_freq(meas_df, top_n, out):
    print("[Phase 11] Machine report text frequency...")

    report_cols = [c for c in meas_df.columns if c.startswith("report_")]
    counter = Counter()
    for col in report_cols:
        for val in meas_df[col].dropna():
            val = str(val).strip()
            if val:
                counter[val] += 1

    total = len(meas_df)
    phrases = [{"text": text, "count": cnt, "pct": round(cnt / total * 100, 2)}
               for text, cnt in counter.most_common(top_n)]
    write_json({"total_records": total, "total_unique_phrases": len(counter),
                "report_columns": len(report_cols), "phrases": phrases},
               out / "report_text_freq.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 12 — Cart Usage
# ─────────────────────────────────────────────────────────────────────────────

def cart_usage(meas_df, top_n, out):
    print("[Phase 12] ECG cart usage...")

    if "cart_id" not in meas_df.columns:
        return
    counts = meas_df["cart_id"].value_counts()
    total = len(meas_df)

    top_carts = [{"cart_id": str(c), "count": int(n), "pct": round(n / total * 100, 2)}
                 for c, n in counts.head(top_n).items()]

    buckets = [("1",    1,    1), ("2–10",  2,   10), ("11–50",  11,  50),
               ("51–200",51, 200), ("201–1000",201,1000), ("1001+",1001,999999)]
    hist = [{"bucket": lbl, "count": int(((counts >= lo) & (counts <= hi)).sum())}
            for lbl, lo, hi in buckets]

    write_json({"total_carts": int(counts.nunique()), "top_carts": top_carts,
                "histogram": hist}, out / "cart_usage.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 13 — Bandwidth & Filtering
# ─────────────────────────────────────────────────────────────────────────────

def bandwidth_filtering(meas_df, out):
    print("[Phase 13] Bandwidth & filtering profiles...")

    total = len(meas_df)
    result = {}
    for field in ("bandwidth", "filtering"):
        if field not in meas_df.columns:
            continue
        vc = meas_df[field].fillna("(missing)").value_counts()
        result[field] = [{"value": str(v), "count": int(c), "pct": round(c / total * 100, 2)}
                         for v, c in vc.items()]
    write_json(result, out / "bandwidth_filtering.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 14 — Note Link Coverage
# ─────────────────────────────────────────────────────────────────────────────

def note_link_coverage(records_df, links_df, out):
    print("[Phase 14] Note link coverage...")

    rec_ids  = set(records_df["study_id"])
    linked   = links_df[links_df["study_id"].isin(rec_ids)]
    linked_ids = set(linked["study_id"])

    notes_per_ecg = linked.groupby("study_id").size()
    buckets = [("1", 1, 1), ("2–5", 2, 5), ("6–10", 6, 10), ("11+", 11, 99999)]
    hist = [{"bucket": lbl, "count": int(((notes_per_ecg >= lo) & (notes_per_ecg <= hi)).sum())}
            for lbl, lo, hi in buckets]

    result = {
        "total_links":          int(len(linked)),
        "records_with_links":   int(len(linked_ids)),
        "records_without_links":int(len(rec_ids - linked_ids)),
        "patients_with_links":  int(linked["subject_id"].nunique()),
        "histogram": hist,
    }
    write_json(result, out / "note_link_coverage.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 15 — Waveform Header Stats (sample)
# ─────────────────────────────────────────────────────────────────────────────

def waveform_header_stats(root, records_df, sample_n, out):
    print(f"[Phase 15] Waveform header stats (sample={sample_n})...")

    try:
        import wfdb
    except ImportError:
        print("  wfdb not available; skipping")
        return

    paths = records_df["path"].dropna().tolist()
    if len(paths) > sample_n:
        paths = random.sample(paths, sample_n)

    sampling_rates = Counter()
    sample_counts  = Counter()
    leads_n        = Counter()
    bit_depths     = Counter()
    resolutions    = Counter()

    for rel in tqdm(paths, desc="  .hea stats"):
        hea_file = root / (str(rel) + ".hea")
        if not hea_file.exists():
            continue
        try:
            hdr = wfdb.rdheader(str(root / rel))
            sampling_rates[int(hdr.fs)] += 1
            sample_counts[int(hdr.sig_len)] += 1
            leads_n[int(hdr.n_sig)] += 1
            if hdr.fmt:
                bit_depths[str(hdr.fmt[0])] += 1
            if hdr.adc_gain:
                resolutions[str(round(hdr.adc_gain[0], 1))] += 1
        except Exception:
            pass

    write_json({
        "sample_size":    len(paths),
        "sampling_rates": {str(k): v for k, v in sampling_rates.items()},
        "sample_counts":  {str(k): v for k, v in sample_counts.items()},
        "leads_counts":   {str(k): v for k, v in leads_n.items()},
        "bit_depths":     {str(k): v for k, v in bit_depths.items()},
        "resolutions":    {str(k): v for k, v in resolutions.items()},
    }, out / "waveform_header_stats.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 16 — Lead Completeness (full scan of all .hea files)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_hea_leads(hea_path: Path):
    """Return list of normalised lead names from a .hea file, or None on error."""
    try:
        lines = hea_path.read_text(errors="replace").splitlines()
        if len(lines) < 2:
            return None
        fields = lines[0].split()
        if len(fields) < 2:
            return None
        n_sig = int(fields[1])
        leads = []
        for line in lines[1: n_sig + 1]:
            parts = line.strip().split()
            if not parts:
                continue
            raw = parts[-1]
            # Skip comment lines
            if raw.startswith("#"):
                continue
            leads.append(LEAD_NORM.get(raw.upper(), raw))
        return leads
    except Exception:
        return None


def lead_completeness(root, records_df, out):
    print(f"[Phase 16] Lead completeness (scanning {len(records_df):,} records)...")

    expected_set = set(EXPECTED_LEADS)
    total_scanned = 0
    records_12 = records_fewer = records_more = nonstandard_order = 0
    per_lead_absent = Counter()
    incomplete = []

    for _, row in tqdm(records_df.iterrows(), total=len(records_df), desc="  .hea scan"):
        hea_path = root / (str(row["path"]) + ".hea")
        if not hea_path.exists():
            continue
        leads = _parse_hea_leads(hea_path)
        if leads is None:
            continue
        total_scanned += 1
        leads_set = set(leads)
        n = len(leads)

        if n == 12:
            records_12 += 1
        elif n < 12:
            records_fewer += 1
        else:
            records_more += 1

        missing = [l for l in EXPECTED_LEADS if l not in leads_set]
        for l in missing:
            per_lead_absent[l] += 1

        if not missing and leads != EXPECTED_LEADS:
            nonstandard_order += 1

        if missing and len(incomplete) < 500:
            incomplete.append({
                "study_id":     int(row["study_id"]),
                "leads_present": leads,
                "leads_missing": missing,
            })

    per_lead = {}
    for lead in EXPECTED_LEADS:
        absent = per_lead_absent[lead]
        per_lead[lead] = {
            "absent_count": absent,
            "absent_pct":   round(absent / total_scanned * 100, 4) if total_scanned else 0,
        }

    write_json({
        "total_scanned":              total_scanned,
        "records_with_12_leads":      records_12,
        "records_with_fewer_leads":   records_fewer,
        "records_with_more_leads":    records_more,
        "nonstandard_lead_order_count": nonstandard_order,
        "per_lead_absence":           per_lead,
        "incomplete_records":         incomplete,
    }, out / "lead_completeness.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 17 — Signal Quality (sampled .dat reads)
# ─────────────────────────────────────────────────────────────────────────────

def signal_quality(root, records_df, sample_n, flat_threshold,
                   nan_count_threshold, clip_pct_thresh, out):
    print(f"[Phase 17] Signal quality (sample={sample_n})...")

    try:
        import wfdb
    except ImportError:
        print("  wfdb not available; skipping")
        return

    items = records_df[["study_id", "path"]].dropna().to_dict("records")
    if len(items) > sample_n:
        items = random.sample(items, sample_n)

    per_lead_flat    = Counter()
    per_lead_dropout = Counter()
    per_lead_clip    = Counter()
    records_with_issue = 0
    flagged_records  = []
    n_ok = 0

    for item in tqdm(items, desc="  signal quality"):
        rec_path = str(root / item["path"])
        try:
            signals, fields = wfdb.rdsamp(rec_path)
        except Exception:
            continue
        n_ok += 1
        sig_names = [LEAD_NORM.get(s.upper(), s) for s in (fields.get("sig_name") or [])]
        n_samples  = signals.shape[0]
        issues_this = {}

        for i, lead in enumerate(sig_names):
            sig   = signals[:, i]
            clean = sig[~np.isnan(sig)]
            issue = []

            n_nan = int(np.sum(np.isnan(sig)))
            if n_nan >= nan_count_threshold:
                issue.append("nan")
                per_lead_dropout[lead] += 1

            if len(clean) == 0:
                pass  # already flagged as nan above
            else:
                if np.std(clean) < flat_threshold:
                    issue.append("flat")
                    per_lead_flat[lead] += 1
                lo, hi = clean.min(), clean.max()
                if hi > lo and np.mean((clean == lo) | (clean == hi)) * 100 > clip_pct_thresh:
                    issue.append("clipped")
                    per_lead_clip[lead] += 1

            if issue:
                issues_this[lead] = issue

        if issues_this:
            records_with_issue += 1
            if len(flagged_records) < 200:
                flagged_records.append({
                    "study_id": int(item["study_id"]),
                    "issues":   issues_this,
                })

    per_lead_issues = {}
    for lead in EXPECTED_LEADS:
        per_lead_issues[lead] = {
            "flat_count":    per_lead_flat[lead],
            "flat_pct":      round(per_lead_flat[lead]    / n_ok * 100, 2) if n_ok else 0,
            "dropout_count": per_lead_dropout[lead],
            "dropout_pct":   round(per_lead_dropout[lead] / n_ok * 100, 2) if n_ok else 0,
            "clip_count":    per_lead_clip[lead],
            "clip_pct":      round(per_lead_clip[lead]    / n_ok * 100, 2) if n_ok else 0,
        }

    write_json({
        "sample_size":            n_ok,
        "records_with_any_issue": records_with_issue,
        "issue_pct":              round(records_with_issue / n_ok * 100, 2) if n_ok else 0,
        "per_lead_issues":        per_lead_issues,
        "flagged_records":        flagged_records,
    }, out / "signal_quality.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18 — Clean Record Identification
# ─────────────────────────────────────────────────────────────────────────────

def clean_records(records_df, meas_df, criteria, out):
    print("[Phase 18] Clean record identification...")

    import json as _json

    all_ids = set(records_df["study_id"])
    excluded = {}   # criterion_name -> set of study_ids excluded by that criterion

    # ── require_all_12_leads ─────────────────────────────────────────────────
    if criteria.get("require_all_12_leads", False):
        lc_path = out / "lead_completeness.json"
        if lc_path.exists():
            lc = _json.loads(lc_path.read_text())
            incomplete_ids = {r["study_id"] for r in lc.get("incomplete_records", [])}
            excluded["missing_leads"] = incomplete_ids & all_ids
        else:
            print("  WARNING: lead_completeness.json not found; skipping require_all_12_leads")
            excluded["missing_leads"] = set()

    # ── no_flat_leads / no_nan_in_leads ──────────────────────────────────────
    sq_path = out / "signal_quality.json"
    if sq_path.exists():
        sq = _json.loads(sq_path.read_text())
        flat_ids = set()
        nan_ids  = set()
        for rec in sq.get("flagged_records", []):
            issues = rec.get("issues", {})
            all_types = [t for types in issues.values() for t in types]
            if "flat" in all_types:
                flat_ids.add(rec["study_id"])
            if "nan" in all_types:
                nan_ids.add(rec["study_id"])
        if criteria.get("no_flat_leads", False):
            excluded["flat_leads"] = flat_ids & all_ids
        if criteria.get("no_nan_in_leads", False):
            excluded["nan_leads"] = nan_ids & all_ids
    else:
        print("  WARNING: signal_quality.json not found; skipping flat/NaN criteria")

    # ── no_missing_metadata ───────────────────────────────────────────────────
    for field in criteria.get("no_missing_metadata", []):
        if field in records_df.columns:
            missing_ids = set(records_df.loc[records_df[field].isna(), "study_id"])
        elif field in meas_df.columns:
            # join on study_id: records not in meas_df at all also excluded
            meas_indexed = meas_df.set_index("study_id")[field]
            # records with no measurement row at all
            no_row = all_ids - set(meas_df["study_id"])
            # records in meas_df but field is null
            null_in_meas = set(meas_indexed[pd.to_numeric(meas_indexed, errors="coerce").isna()
                                            if pd.api.types.is_numeric_dtype(meas_indexed)
                                            else meas_indexed.isna()].index)
            missing_ids = (no_row | null_in_meas) & all_ids
        else:
            print(f"  WARNING: field '{field}' not found in records_df or meas_df; skipping")
            continue
        excluded[f"missing_{field}"] = missing_ids & all_ids

    # ── Compute passing set ────────────────────────────────────────────────────
    excluded_union = set().union(*excluded.values()) if excluded else set()
    passing_ids    = all_ids - excluded_union

    # ── Write clean_records.csv ───────────────────────────────────────────────
    clean_df = records_df[records_df["study_id"].isin(passing_ids)][
        ["study_id", "subject_id", "ecg_time", "path"]
    ].copy()
    csv_path = out.parent / "clean_records.csv"
    clean_df.to_csv(csv_path, index=False)
    print(f"  wrote {csv_path.relative_to(REPO_ROOT)}  ({len(clean_df):,} records)")

    # ── Write summary JSON ────────────────────────────────────────────────────
    summary = {
        "total_records":       len(all_ids),
        "passed_all_criteria": len(passing_ids),
        "excluded_total":      len(excluded_union),
        "exclusions":          {k: len(v) for k, v in excluded.items()},
        "criteria_applied":    {k: bool(v) for k, v in criteria.items()
                                if not isinstance(v, list)},
        "signal_quality_note": (
            "flat/NaN exclusions are based on the sampled signal_quality.json "
            "and may not cover all records"
        ),
    }
    write_json(summary, out / "clean_records_summary.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 19 — Render HTML Report
# ─────────────────────────────────────────────────────────────────────────────

def render_report(data_dir, report_path, template_path, d3_path):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)
    d3_src = d3_path.read_text()

    json_blobs = {}
    for jf in sorted(data_dir.glob("*.json")):
        key = jf.stem.replace("-", "_")
        json_blobs[key] = jf.read_text()

    html = template.render(d3_source=d3_src, json_blobs=json_blobs)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html)
    print(f"  wrote {report_path.relative_to(REPO_ROOT)}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MIMIC-IV ECG analysis script")
    parser.add_argument("--config", default="analysis/mimic_iv_ecg/config.yaml")
    args = parser.parse_args()

    cfg_path = REPO_ROOT / args.config
    cfg = load_config(cfg_path)

    root = Path(cfg["dataset"]["root"])
    out  = REPO_ROOT / cfg["output"]["data_dir"]
    out.mkdir(parents=True, exist_ok=True)

    a = cfg.get("analysis", {})
    max_records   = a.get("max_records")
    sample_wf     = int(a.get("sample_waveforms",       200))
    sample_sq     = int(a.get("sample_signal_quality",  2000))
    top_n_reports = int(a.get("top_n_reports",          40))
    top_n_carts   = int(a.get("top_n_carts",            30))
    miss_thresh   = float(a.get("missing_threshold_pct", 5.0))

    sa = cfg.get("signal_analysis", {})
    flat_threshold       = float(sa.get("flat_threshold",      0.01))
    nan_count_threshold  = int(sa.get("nan_count_threshold",   1))
    clip_pct             = float(sa.get("clip_pct",            1.0))

    criteria = cfg.get("clean_record_criteria", {})

    records_df, meas_df, dict_df, links_df = load_data(root, cfg, max_records)

    dataset_summary(root, records_df, meas_df, links_df, out)
    record_coverage(records_df, meas_df, links_df, out)
    temporal_distribution(records_df, out)
    studies_per_patient(records_df, out)
    measurement_stats(meas_df, out)
    measurement_missing(meas_df, dict_df, miss_thresh, out)
    interval_distributions(meas_df, out)
    axis_distributions(meas_df, out)
    report_text_freq(meas_df, top_n_reports, out)
    cart_usage(meas_df, top_n_carts, out)
    bandwidth_filtering(meas_df, out)
    note_link_coverage(records_df, links_df, out)
    waveform_header_stats(root, records_df, sample_wf, out)
    lead_completeness(root, records_df, out)
    signal_quality(root, records_df, sample_sq, flat_threshold, nan_count_threshold, clip_pct, out)
    clean_records(records_df, meas_df, criteria, out)

    print("[Phase 19] Rendering HTML report...")
    template_path = REPO_ROOT / "scripts" / "report_template_mimic_iv_ecg.html"
    d3_path       = REPO_ROOT / "scripts" / "vendor" / "d3.min.js"
    report_path   = REPO_ROOT / cfg["output"]["report_html"]
    render_report(out, report_path, template_path, d3_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
