#!/usr/bin/env python3
"""
PTB-XL ECG Dataset Analysis Script
Produces JSON data files and a self-contained interactive HTML report (D3.js).

Usage:
    python scripts/analyse_ptbxl.py --config analysis/ptbxl/config.yaml
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import wfdb
import yaml
from jinja2 import Environment, FileSystemLoader
from tqdm import tqdm

LEADS = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# Static PTB-XL directory / file structure for the report tree visualisation
DATASET_TREE = {
    "name": "ptb-xl / 1_0_1 /", "type": "folder",
    "desc": "PTB-XL v1.0.1 root — 21,837 ECG records, 3.2 GB total",
    "children": [
        {"name": "ptbxl_database.csv",  "type": "csv",    "desc": "Main metadata: 21,837 records × 28 columns (demographics, SCP codes, quality flags, fold assignments)"},
        {"name": "scp_statements.csv",  "type": "csv",    "desc": "SCP-ECG diagnostic code reference table (71 codes, descriptions, diagnostic classes)"},
        {"name": "RECORDS",             "type": "text",   "desc": "Plain-text list of all 21,837 record paths (one per line)"},
        {"name": "example_physionet.py","type": "python", "desc": "Official example script showing how to load records with the wfdb library"},
        {"name": "LICENSE.txt",         "type": "text",   "desc": "Creative Commons Attribution 4.0 International (CC BY 4.0)"},
        {"name": "SHA256SUMS.txt",      "type": "text",   "desc": "SHA-256 checksums for all files"},
        {
            "name": "records100 /", "type": "folder",
            "desc": "100 Hz ECG signals — 604 MB total; 24 subdirectories (1,000 records each)",
            "children": [
                {
                    "name": "00000 /", "type": "folder",
                    "desc": "Records with ecg_id 1–999 (example subdirectory)",
                    "children": [
                        {"name": "00001_lr.dat", "type": "dat", "desc": "Binary WFDB signal file — 12 leads × 1,000 samples (10 s @ 100 Hz), 16-bit integers, 24 KB"},
                        {"name": "00001_lr.hea", "type": "hea", "desc": "WFDB plain-text header — signal names, sampling rate, ADC gain, channel metadata"},
                        {"name": "00002_lr.dat", "type": "dat", "desc": "Next record signal file (same format)"},
                        {"name": "00002_lr.hea", "type": "hea", "desc": "Next record header file"},
                        {"name": "… (≈ 996 more pairs)", "type": "ellipsis", "desc": ""},
                    ]
                },
                {"name": "01000 / … 21000 /", "type": "folder-multi",
                 "desc": "23 further subdirectories with the same structure (1,000-record batches)",
                 "children": []},
            ]
        },
        {
            "name": "records500 /", "type": "folder",
            "desc": "500 Hz ECG signals — 2.6 GB total; same 24-subdirectory layout as records100",
            "children": [
                {
                    "name": "00000 /", "type": "folder",
                    "desc": "Records with ecg_id 1–999 (example subdirectory)",
                    "children": [
                        {"name": "00001_hr.dat", "type": "dat", "desc": "Binary WFDB signal file — 12 leads × 5,000 samples (10 s @ 500 Hz), 16-bit integers, 120 KB"},
                        {"name": "00001_hr.hea", "type": "hea", "desc": "WFDB plain-text header for the 500 Hz record"},
                        {"name": "00002_hr.dat", "type": "dat", "desc": "Next record signal file (same format)"},
                        {"name": "00002_hr.hea", "type": "hea", "desc": "Next record header file"},
                        {"name": "… (≈ 996 more pairs)", "type": "ellipsis", "desc": ""},
                    ]
                },
                {"name": "01000 / … 21000 /", "type": "folder-multi",
                 "desc": "23 further subdirectories with the same structure (1,000-record batches)",
                 "children": []},
            ]
        },
    ]
}


# ---------------------------------------------------------------------------
# Phase 1 — Config
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def resolve_paths(cfg: dict, repo_root: Path) -> dict:
    """Make all relative output paths absolute from repo root."""
    for key in ("report_dir", "data_dir", "clean_csv", "report_html"):
        p = Path(cfg["output"][key])
        if not p.is_absolute():
            cfg["output"][key] = str(repo_root / p)
    return cfg


# ---------------------------------------------------------------------------
# Phase 2 — Load Metadata
# ---------------------------------------------------------------------------

def load_metadata(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(cfg["dataset"]["root"])
    db = pd.read_csv(root / cfg["dataset"]["metadata_file"], index_col="ecg_id")
    scp = pd.read_csv(root / cfg["dataset"]["scp_file"], index_col=0)

    # Parse scp_codes from string representation of dict
    db["scp_codes"] = db["scp_codes"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else {}
    )

    # Quality flags: treat any non-NaN value as True
    quality_flags = [
        "baseline_drift", "static_noise", "burst_noise",
        "electrodes_problems", "extra_beats"
    ]
    for flag in quality_flags:
        if flag in db.columns:
            db[flag] = db[flag].notna()

    return db, scp


# ---------------------------------------------------------------------------
# Phase 3 — Metadata Analysis → JSON
# ---------------------------------------------------------------------------

def analyse_metadata(db: pd.DataFrame, scp: pd.DataFrame, cfg: dict) -> dict:
    top_n_scp = cfg["metadata_analysis"]["top_n_scp_codes"]
    top_n_sites = cfg["metadata_analysis"]["top_n_sites"]
    data_dir = Path(cfg["output"]["data_dir"])

    results = {}

    # 1. Summary
    summary = {
        "total_records": int(len(db)),
        "unique_patients": int(db["patient_id"].nunique()),
        "date_range": {
            "min": str(db["recording_date"].min()),
            "max": str(db["recording_date"].max()),
        },
        "leads": LEADS,
        "folds": sorted(db["strat_fold"].dropna().unique().astype(int).tolist()),
        "sampling_rates": ["100 Hz", "500 Hz"],
    }
    _write_json(data_dir / "metadata_summary.json", summary)
    results["summary"] = summary

    # 2. Age distribution (histogram bins)
    ages = db["age"].dropna()
    counts, edges = np.histogram(ages, bins=20)
    age_dist = [
        {"bin_start": float(edges[i]), "bin_end": float(edges[i + 1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]
    _write_json(data_dir / "age_distribution.json", {
        "bins": age_dist,
        "stats": {
            "mean": round(float(ages.mean()), 1),
            "median": round(float(ages.median()), 1),
            "std": round(float(ages.std()), 1),
            "min": int(ages.min()),
            "max": int(ages.max()),
            "missing": int(db["age"].isna().sum()),
        }
    })

    # 3. Sex distribution
    sex_map = {0: "Female", 1: "Male"}
    sex_counts = db["sex"].map(sex_map).value_counts()
    sex_data = [{"label": k, "count": int(v)} for k, v in sex_counts.items()]
    _write_json(data_dir / "sex_distribution.json", {
        "data": sex_data,
        "missing": int(db["sex"].isna().sum()),
    })

    # 4. Height & weight scatter (sample up to 5000 points)
    hw = db[["height", "weight"]].dropna()
    sample = hw.sample(min(5000, len(hw)), random_state=42)
    _write_json(data_dir / "height_weight.json", {
        "data": [{"height": float(r.height), "weight": float(r.weight)}
                 for r in sample.itertuples()],
        "stats": {
            "height": {"mean": round(float(hw["height"].mean()), 1),
                       "std": round(float(hw["height"].std()), 1),
                       "missing": int(db["height"].isna().sum())},
            "weight": {"mean": round(float(hw["weight"].mean()), 1),
                       "std": round(float(hw["weight"].std()), 1),
                       "missing": int(db["weight"].isna().sum())},
        }
    })

    # 5. Recording site
    site_counts = db["site"].value_counts().head(top_n_sites)
    _write_json(data_dir / "recording_site.json", {
        "data": [{"label": str(k), "count": int(v)} for k, v in site_counts.items()],
        "missing": int(db["site"].isna().sum()),
    })

    # 6. Strat fold distribution
    fold_counts = db["strat_fold"].dropna().astype(int).value_counts().sort_index()
    _write_json(data_dir / "strat_fold.json", {
        "data": [{"fold": int(k), "count": int(v)} for k, v in fold_counts.items()],
        "missing": int(db["strat_fold"].isna().sum()),
    })

    # 7. Top-N SCP codes
    all_codes: dict[str, int] = {}
    for codes in db["scp_codes"]:
        for code in codes:
            all_codes[code] = all_codes.get(code, 0) + 1
    top_codes = sorted(all_codes.items(), key=lambda x: x[1], reverse=True)[:top_n_scp]
    _write_json(data_dir / "scp_top_codes.json", {
        "data": [{"code": c, "count": n,
                  "description": str(scp.loc[c, "description"]) if c in scp.index else c}
                 for c, n in top_codes],
        "total_unique_codes": len(all_codes),
    })

    # 8. Diagnostic class distribution (from scp_statements)
    diag_scp = scp[scp["diagnostic"] == 1.0]
    class_counts: dict[str, int] = {}
    for codes in db["scp_codes"]:
        seen = set()
        for code, conf in codes.items():
            if code in diag_scp.index and conf > 0:
                dc = str(diag_scp.loc[code, "diagnostic_class"])
                if dc not in seen:
                    class_counts[dc] = class_counts.get(dc, 0) + 1
                    seen.add(dc)
    _write_json(data_dir / "diagnostic_class.json", {
        "data": [{"label": k, "count": v}
                 for k, v in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)]
    })

    # 9. Heart axis
    axis_counts = db["heart_axis"].dropna().value_counts()
    _write_json(data_dir / "heart_axis.json", {
        "data": [{"label": str(k), "count": int(v)} for k, v in axis_counts.items()],
        "missing": int(db["heart_axis"].isna().sum()),
    })

    # 10. Quality flags
    quality_flags = [
        "baseline_drift", "static_noise", "burst_noise",
        "electrodes_problems", "extra_beats"
    ]
    flag_data = []
    for flag in quality_flags:
        if flag in db.columns:
            flag_data.append({"flag": flag, "count": int(db[flag].sum())})
    _write_json(data_dir / "quality_flags.json", {"data": flag_data})

    # Dataset tree structure
    _write_json(data_dir / "dataset_tree.json", DATASET_TREE)

    print(f"[Phase 3] Metadata analysis complete. {len(db)} records.")
    return results


# ---------------------------------------------------------------------------
# Phase 4 — Missing Metadata Analysis → JSON
# ---------------------------------------------------------------------------

def analyse_missing_metadata(db: pd.DataFrame, cfg: dict) -> None:
    data_dir = Path(cfg["output"]["data_dir"])
    sample_size = cfg["metadata_analysis"]["missing_heatmap_sample_size"]

    # Exclude signal path columns and scp_codes (always present as parsed dict)
    exclude = {"filename_lr", "filename_hr", "scp_codes"}
    cols = [c for c in db.columns if c not in exclude]

    total = len(db)
    missing_pct = []
    for col in cols:
        n_missing = int(db[col].isna().sum())
        missing_pct.append({
            "column": col,
            "missing_count": n_missing,
            "missing_pct": round(100 * n_missing / total, 2),
        })
    missing_pct.sort(key=lambda x: x["missing_pct"], reverse=True)

    # Heatmap: sampled binary presence matrix
    sample = db[cols].sample(min(sample_size, total), random_state=42)
    heatmap_rows = []
    for ecg_id, row in sample.iterrows():
        heatmap_rows.append({
            "ecg_id": int(ecg_id),
            "values": [1 if pd.isna(v) else 0 for v in row],
        })

    _write_json(data_dir / "missing_metadata.json", {
        "columns": cols,
        "summary": missing_pct,
        "heatmap": heatmap_rows,
    })
    print(f"[Phase 4] Missing metadata analysis complete.")


# ---------------------------------------------------------------------------
# Phase 5 — ECG Signal Analysis → JSON
# ---------------------------------------------------------------------------

def analyse_signals(db: pd.DataFrame, cfg: dict) -> dict[int, dict]:
    data_dir = Path(cfg["output"]["data_dir"])
    root = Path(cfg["dataset"]["root"])
    resolution = cfg["dataset"]["signal_resolution"]
    max_records = cfg["dataset"]["max_records"]
    flat_thr = cfg["signal_analysis"]["flat_threshold"]
    nan_thr = cfg["signal_analysis"]["nan_count_threshold"]

    suffix = "lr" if resolution == 100 else "hr"
    fn_col = f"filename_{suffix}"

    records = db[fn_col].dropna()
    if max_records:
        records = records.head(int(max_records))

    # Per-lead aggregates
    nan_counts = {lead: 0 for lead in LEADS}    # records with NaN in this lead
    flat_counts = {lead: 0 for lead in LEADS}   # records with flat signal
    missing_lead_counts = {lead: 0 for lead in LEADS}  # lead completely absent

    # Per-record signal flags (for heatmap, sampled later)
    per_record: list[dict] = []
    load_errors = 0

    for ecg_id, filepath in tqdm(records.items(), desc="Analysing ECG signals", unit="rec"):
        abs_path = str(root / filepath)
        try:
            signals, fields = wfdb.rdsamp(abs_path)
        except Exception:
            load_errors += 1
            per_record.append({
                "ecg_id": int(ecg_id),
                "load_error": True,
                "nan_leads": [],
                "flat_leads": [],
                "missing_leads": LEADS[:],
            })
            for lead in LEADS:
                missing_lead_counts[lead] += 1
            continue

        sig_names = [s.strip() for s in fields["sig_name"]]
        rec_nan = []
        rec_flat = []
        rec_missing = []

        for lead in LEADS:
            if lead not in sig_names:
                missing_lead_counts[lead] += 1
                rec_missing.append(lead)
                continue

            idx = sig_names.index(lead)
            col = signals[:, idx].astype(float)
            n_nan = int(np.isnan(col).sum())
            if n_nan >= nan_thr:
                nan_counts[lead] += 1
                rec_nan.append(lead)
            valid = col[~np.isnan(col)]
            if len(valid) == 0 or float(np.std(valid)) < flat_thr:
                flat_counts[lead] += 1
                rec_flat.append(lead)

        per_record.append({
            "ecg_id": int(ecg_id),
            "load_error": False,
            "nan_leads": rec_nan,
            "flat_leads": rec_flat,
            "missing_leads": rec_missing,
        })

    n_analysed = len(records)

    # Missing leads bar
    missing_leads_data = [
        {"lead": lead, "count": missing_lead_counts[lead],
         "pct": round(100 * missing_lead_counts[lead] / n_analysed, 3)}
        for lead in LEADS
    ]

    # NaN leads bar
    nan_leads_data = [
        {"lead": lead, "count": nan_counts[lead],
         "pct": round(100 * nan_counts[lead] / n_analysed, 3)}
        for lead in LEADS
    ]

    # Flat leads bar
    flat_leads_data = [
        {"lead": lead, "count": flat_counts[lead],
         "pct": round(100 * flat_counts[lead] / n_analysed, 3)}
        for lead in LEADS
    ]

    # Heatmap sample (2000 records max)
    sample_size = cfg["metadata_analysis"]["missing_heatmap_sample_size"]
    heatmap_sample = per_record[:sample_size]  # already ordered, no need to shuffle
    heatmap_rows = [
        {"ecg_id": r["ecg_id"],
         "values": [1 if (lead in r["nan_leads"] or lead in r["missing_leads"]) else 0
                    for lead in LEADS]}
        for r in heatmap_sample
    ]

    _write_json(data_dir / "missing_ecg_leads.json", {
        "leads": LEADS,
        "n_analysed": n_analysed,
        "load_errors": load_errors,
        "missing_leads": missing_leads_data,
        "nan_leads": nan_leads_data,
        "heatmap": heatmap_rows,
    })
    _write_json(data_dir / "flat_signal_leads.json", {
        "leads": LEADS,
        "n_analysed": n_analysed,
        "data": flat_leads_data,
    })

    print(f"[Phase 5] Signal analysis complete. {n_analysed} records, {load_errors} load errors.")

    # Return per-record dict keyed by ecg_id for use in Phase 6
    return {r["ecg_id"]: r for r in per_record}


# ---------------------------------------------------------------------------
# Phase 6 — Clean Record Identification
# ---------------------------------------------------------------------------

def identify_clean_records(db: pd.DataFrame, signal_flags: dict[int, dict],
                           cfg: dict) -> pd.DataFrame:
    data_dir = Path(cfg["output"]["data_dir"])
    clean_csv = Path(cfg["output"]["clean_csv"])
    criteria = cfg["clean_record_criteria"]
    required_meta = criteria.get("no_missing_metadata") or []
    exclude_flags = criteria.get("exclude_quality_flags") or []

    clean_ids = []
    for ecg_id, row in db.iterrows():
        # Metadata completeness
        meta_ok = all(
            not (pd.isna(row[col]) if col in db.columns else True)
            for col in required_meta
        )
        if not meta_ok:
            continue

        # Quality flags
        flags_ok = all(not row.get(flag, False) for flag in exclude_flags)
        if not flags_ok:
            continue

        # Signal flags
        sig = signal_flags.get(int(ecg_id))
        if sig is None:
            # Record not analysed (beyond max_records cap) — skip
            continue
        if sig.get("load_error"):
            continue
        if criteria.get("require_all_12_leads") and sig["missing_leads"]:
            continue
        if criteria.get("no_nan_in_leads") and sig["nan_leads"]:
            continue
        if criteria.get("no_flat_leads") and sig["flat_leads"]:
            continue

        clean_ids.append({"ecg_id": int(ecg_id),
                          "strat_fold": int(row["strat_fold"])})

    clean_df = pd.DataFrame(clean_ids)
    clean_df.to_csv(clean_csv, index=False)
    print(f"[Phase 6] Clean records: {len(clean_df)} / {len(db)} "
          f"({100*len(clean_df)/len(db):.1f}%)")

    # Per-fold breakdown for chart
    total_per_fold = db["strat_fold"].dropna().astype(int).value_counts().sort_index()
    clean_per_fold = clean_df.groupby("strat_fold").size() if len(clean_df) else pd.Series(dtype=int)
    fold_data = []
    for fold in sorted(total_per_fold.index):
        total = int(total_per_fold.get(fold, 0))
        clean = int(clean_per_fold.get(fold, 0))
        fold_data.append({
            "fold": int(fold),
            "clean": clean,
            "dirty": total - clean,
            "total": total,
        })
    _write_json(data_dir / "clean_records_per_fold.json", {"data": fold_data})

    return clean_df


# ---------------------------------------------------------------------------
# Phase 7/8 — Generate HTML Report
# ---------------------------------------------------------------------------

def generate_report(cfg: dict) -> None:
    report_html = Path(cfg["output"]["report_html"])
    data_dir = Path(cfg["output"]["data_dir"])
    template_path = Path(__file__).parent / "report_template.html"
    vendor_d3 = Path(__file__).parent / "vendor" / "d3.min.js"

    # Load D3 source
    d3_src = vendor_d3.read_text()

    # Inline all JSON data files as JS variables
    json_vars: dict[str, str] = {}
    for json_file in sorted(data_dir.glob("*.json")):
        var_name = json_file.stem.replace("-", "_")
        json_vars[var_name] = json_file.read_text()

    # Inline clean_records.csv content
    clean_csv = Path(cfg["output"]["clean_csv"])
    clean_csv_content = clean_csv.read_text() if clean_csv.exists() else "ecg_id,strat_fold\n"

    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)
    html = template.render(d3_src=d3_src, json_vars=json_vars, clean_csv_content=clean_csv_content)

    report_html.parent.mkdir(parents=True, exist_ok=True)
    report_html.write_text(html)
    print(f"[Phase 8] Report written → {report_html}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_json_default)


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Not serializable: {type(obj)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Analyse PTB-XL ECG dataset")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    cfg = load_config(args.config)
    cfg = resolve_paths(cfg, repo_root)

    # Ensure output dirs exist
    Path(cfg["output"]["data_dir"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["output"]["report_dir"]).mkdir(parents=True, exist_ok=True)

    print("=== PTB-XL Analysis ===")

    print("[Phase 2] Loading metadata...")
    db, scp = load_metadata(cfg)

    print("[Phase 3] Analysing metadata...")
    analyse_metadata(db, scp, cfg)

    print("[Phase 4] Analysing missing metadata...")
    analyse_missing_metadata(db, cfg)

    print("[Phase 5] Analysing ECG signals (this may take a while)...")
    signal_flags = analyse_signals(db, cfg)

    print("[Phase 6] Identifying clean records...")
    identify_clean_records(db, signal_flags, cfg)

    print("[Phase 7/8] Generating HTML report...")
    generate_report(cfg)

    print("=== Done ===")


if __name__ == "__main__":
    main()
