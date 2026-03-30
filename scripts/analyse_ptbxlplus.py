#!/usr/bin/env python3
"""
PTB-XL+ Dataset Analysis Script
Produces JSON data files and a self-contained D3.js HTML report.

Usage:
    python scripts/analyse_ptbxlplus.py --config analysis/ptbxlplus/config.yaml
"""
import argparse
import ast
import json
import os
import sys
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def resolve(cfg_root: Path, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else cfg_root / rel


def safe_parse(val):
    """Parse a string representation of a Python literal."""
    if pd.isna(val):
        return []
    try:
        return ast.literal_eval(val)
    except Exception:
        return []


def write_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Load data
# ─────────────────────────────────────────────────────────────────────────────

def load_features(root: Path, cfg: dict):
    feat_cfg = cfg["dataset"]["features"]
    dfs = {}
    for src in ("12sl", "ecgdeli", "unig"):
        p = root / feat_cfg[src]
        df = pd.read_csv(p)
        dfs[src] = df
        print(f"  {src} features: {df.shape}")
    desc = pd.read_csv(root / feat_cfg["description"])
    return dfs, desc


def load_labels(root: Path, cfg: dict):
    lbl_cfg = cfg["dataset"]["labels"]
    ptbxl = pd.read_csv(root / lbl_cfg["ptbxl"])
    sl12 = pd.read_csv(root / lbl_cfg["12sl"])
    snomed = pd.read_csv(root / lbl_cfg["snomed"])
    map_ptbxl = pd.read_csv(root / lbl_cfg["mapping_ptbxl"], on_bad_lines="skip")
    map_12sl = pd.read_csv(root / lbl_cfg["mapping_12sl"], on_bad_lines="skip")
    print(f"  ptbxl labels: {len(ptbxl)} rows")
    print(f"  12sl labels:  {len(sl12)} rows")
    print(f"  snomed:       {len(snomed)} rows")
    return ptbxl, sl12, snomed, map_ptbxl, map_12sl


def scan_fiducial(root: Path, cfg: dict):
    fid_dir = root / cfg["dataset"]["fiducial_points"]["ecgdeli"]
    record_ids = set()
    for sub in fid_dir.iterdir():
        if sub.is_dir():
            for f in sub.glob("*_points_global.atr"):
                rid = f.stem.replace("_points_global", "")
                record_ids.add(rid)
    print(f"  fiducial records: {len(record_ids)}")
    return fid_dir, record_ids


def scan_median_beats(root: Path, cfg: dict):
    mb_cfg = cfg["dataset"]["median_beats"]
    results = {}
    for src in ("12sl", "unig"):
        mb_dir = root / mb_cfg[src]
        record_ids = set()
        for sub in mb_dir.iterdir():
            if sub.is_dir():
                for f in sub.glob("*_medians.hea"):
                    rid = f.stem.replace("_medians", "")
                    record_ids.add(rid)
        results[src] = {"dir": mb_dir, "records": record_ids}
        print(f"  {src} median beats: {len(record_ids)} records")
    return results


def load_records_file(root: Path, cfg: dict):
    rfile = root / cfg["dataset"]["records_file"]
    records = [line.strip() for line in rfile.read_text().splitlines() if line.strip()]
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Dataset summary
# ─────────────────────────────────────────────────────────────────────────────

def compute_summary(feat_dfs, ptbxl_lbl, sl12_lbl, snomed_df,
                    fid_ids, mb_data, records_list, out: Path):
    # ecg_id column presence — features don't have ecg_id as column, they are 0-indexed rows
    # check if ecg_id is a column or use row index
    def n_rows(df):
        return len(df)

    unique_snomed_ptbxl = set()
    for v in ptbxl_lbl["scp_codes_ext_snomed"].dropna():
        for sid, _ in safe_parse(v):
            unique_snomed_ptbxl.add(int(sid))

    unique_snomed_12sl = set()
    for v in sl12_lbl["statements_ext_snomed"].dropna():
        for sid, _ in safe_parse(v):
            unique_snomed_12sl.add(int(sid))

    # 12sl feature ecg_ids come from ecgdeli (which has ecg_id col)
    ecgdeli_has_id = "ecg_id" in feat_dfs["ecgdeli"].columns
    sl12feat_has_id = "ecg_id" in feat_dfs["12sl"].columns

    summary = {
        "features": {
            "12sl":    {"records": n_rows(feat_dfs["12sl"]),   "features": feat_dfs["12sl"].shape[1]},
            "ecgdeli": {"records": n_rows(feat_dfs["ecgdeli"]), "features": feat_dfs["ecgdeli"].shape[1]},
            "unig":    {"records": n_rows(feat_dfs["unig"]),   "features": feat_dfs["unig"].shape[1]},
        },
        "labels": {
            "ptbxl_records": len(ptbxl_lbl),
            "12sl_records":  len(sl12_lbl),
        },
        "snomed": {
            "total_in_description": len(snomed_df),
            "unique_in_ptbxl":  len(unique_snomed_ptbxl),
            "unique_in_12sl":   len(unique_snomed_12sl),
            "unique_in_both":   len(unique_snomed_ptbxl & unique_snomed_12sl),
        },
        "fiducial_points": {
            "records_with_global": len(fid_ids),
        },
        "median_beats": {
            "12sl_records": len(mb_data["12sl"]["records"]),
            "unig_records": len(mb_data["unig"]["records"]),
        },
        "canonical_records": len(records_list),
    }
    write_json(summary, out / "dataset_summary.json")
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — Record coverage
# ─────────────────────────────────────────────────────────────────────────────

def compute_record_coverage(feat_dfs, ptbxl_lbl, sl12_lbl, fid_ids, mb_data, records_list, out: Path):
    # Canonical IDs from RECORDS file (extract numeric part)
    canonical = set()
    for r in records_list:
        stem = Path(r).stem  # e.g. "021359_medians" or "00001_medians"
        num = stem.replace("_medians", "")
        # normalise to int
        try:
            canonical.add(int(num))
        except ValueError:
            pass

    def ids_from_ecgdeli(df):
        if "ecg_id" in df.columns:
            return set(df["ecg_id"].dropna().astype(int))
        return set(range(1, len(df) + 1))

    ptbxl_ids = set(ptbxl_lbl["ecg_id"].dropna().astype(int))
    sl12_ids  = set(sl12_lbl["ecg_id"].dropna().astype(int))
    ecgdeli_ids = ids_from_ecgdeli(feat_dfs["ecgdeli"])

    # 12sl/unig features don't have ecg_id — assume sequential
    sl12feat_ids = set(range(1, len(feat_dfs["12sl"]) + 1))
    unig_ids     = set(range(1, len(feat_dfs["unig"]) + 1))

    fid_int  = {int(r) for r in fid_ids}
    mb12_int = set()
    for r in mb_data["12sl"]["records"]:
        try:
            mb12_int.add(int(r))
        except ValueError:
            pass
    mbun_int = set()
    for r in mb_data["unig"]["records"]:
        try:
            mbun_int.add(int(r))
        except ValueError:
            pass

    sources = {
        "ptbxl_labels":    ptbxl_ids,
        "12sl_labels":     sl12_ids,
        "12sl_features":   sl12feat_ids,
        "ecgdeli_features": ecgdeli_ids,
        "unig_features":   unig_ids,
        "fiducial_ecgdeli": fid_int,
        "median_beats_12sl": mb12_int,
        "median_beats_unig": mbun_int,
    }

    coverage = {
        "canonical_count": len(canonical),
        "sources": {}
    }
    for name, ids in sources.items():
        missing = sorted(canonical - ids)[:20]  # first 20 missing
        coverage["sources"][name] = {
            "count": len(ids),
            "missing_from_canonical": len(canonical - ids),
            "missing_examples": missing,
        }

    # Records present in all sources
    all_ids = ptbxl_ids & sl12_ids & ecgdeli_ids & fid_int & mb12_int & mbun_int
    coverage["present_in_all_sources"] = len(all_ids)

    write_json(coverage, out / "record_coverage.json")
    return coverage


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — Feature analysis
# ─────────────────────────────────────────────────────────────────────────────

def compute_feature_missing(feat_dfs, desc_df, threshold_pct: float, out: Path):
    # Build description lookup
    desc_cols = list(desc_df.columns)
    # first col is feature id pattern
    id_col = desc_cols[0]

    for src, df in feat_dfs.items():
        missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
        rows = []
        for feat, pct in missing_pct.items():
            row = {"feature": feat, "missing_pct": round(float(pct), 3), "flagged": pct > threshold_pct}
            rows.append(row)
        result = {
            "source": src,
            "threshold_pct": threshold_pct,
            "total_features": len(rows),
            "flagged_count": sum(1 for r in rows if r["flagged"]),
            "features": rows,
        }
        write_json(result, out / f"feature_missing_{src}.json")


def compute_feature_stats(feat_dfs, desc_df, out: Path):
    # Key clinical features to report stats for (common across sources)
    # We'll pick features matching these patterns
    key_patterns = [
        "P_Dur", "QRS_Dur", "QT_Int", "PR_Int", "PQ_Int",
        "P_Amp", "R_Amp", "T_Amp", "QRS_Amp",
        "RR_Int", "HR",
    ]

    for src, df in feat_dfs.items():
        stats_rows = []
        for col in df.columns:
            matched = any(pat.lower() in col.lower() for pat in key_patterns)
            if not matched:
                continue
            series = df[col].dropna()
            if len(series) == 0:
                continue
            stats_rows.append({
                "feature": col,
                "count": int(len(series)),
                "missing_pct": round(float((len(df) - len(series)) / len(df) * 100), 2),
                "mean": round(float(series.mean()), 4),
                "std":  round(float(series.std()), 4),
                "min":  round(float(series.min()), 4),
                "p25":  round(float(series.quantile(0.25)), 4),
                "p50":  round(float(series.median()), 4),
                "p75":  round(float(series.quantile(0.75)), 4),
                "max":  round(float(series.max()), 4),
            })
        result = {"source": src, "features": stats_rows}
        write_json(result, out / f"feature_stats_{src}.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 6 — Label analysis
# ─────────────────────────────────────────────────────────────────────────────

def compute_label_freq(ptbxl_lbl, sl12_lbl, snomed_df, top_n: int, out: Path):
    # Build snomed_id → description lookup
    snomed_lookup = {}
    if "snomed_id" in snomed_df.columns and "description" in snomed_df.columns:
        for _, row in snomed_df.iterrows():
            snomed_lookup[int(row["snomed_id"])] = str(row["description"])

    # PTB-XL SCP codes
    scp_counter = Counter()
    for val in ptbxl_lbl["scp_codes"].dropna():
        for code, conf in safe_parse(val):
            scp_counter[code] += 1

    total_ptbxl = len(ptbxl_lbl)
    ptbxl_rows = []
    for code, cnt in scp_counter.most_common(top_n):
        ptbxl_rows.append({
            "code": code,
            "count": cnt,
            "pct": round(cnt / total_ptbxl * 100, 2),
        })
    write_json({"source": "ptbxl", "total_records": total_ptbxl, "labels": ptbxl_rows},
               out / "ptbxl_label_freq.json")

    # 12SL statements
    stmt_counter = Counter()
    for val in sl12_lbl["statements"].dropna():
        for code in safe_parse(val):
            stmt_counter[code] += 1

    total_12sl = len(sl12_lbl)
    sl12_rows = []
    for code, cnt in stmt_counter.most_common(top_n):
        sl12_rows.append({
            "code": code,
            "count": cnt,
            "pct": round(cnt / total_12sl * 100, 2),
        })
    write_json({"source": "12sl", "total_records": total_12sl, "labels": sl12_rows},
               out / "12sl_label_freq.json")


def compute_label_cooccurrence(ptbxl_lbl, sl12_lbl, top_n: int, out: Path):
    def build_cooccurrence(df, col, parser, top_n):
        # Count top labels
        counter = Counter()
        records_labels = []
        for val in df[col].dropna():
            labels = parser(val)
            records_labels.append(labels)
            for lbl in labels:
                counter[lbl] += 1
        top_labels = [lbl for lbl, _ in counter.most_common(top_n)]
        label_idx = {lbl: i for i, lbl in enumerate(top_labels)}
        n = len(top_labels)
        matrix = [[0] * n for _ in range(n)]
        for labels in records_labels:
            present = [label_idx[l] for l in labels if l in label_idx]
            for i in present:
                for j in present:
                    matrix[i][j] += 1
        return top_labels, matrix

    # PTB-XL
    def ptbxl_parser(val):
        return [code for code, _ in safe_parse(val)]

    # 12SL
    def sl12_parser(val):
        return safe_parse(val) if isinstance(safe_parse(val), list) else []

    ptbxl_labels, ptbxl_matrix = build_cooccurrence(ptbxl_lbl, "scp_codes", ptbxl_parser, top_n)
    sl12_labels, sl12_matrix = build_cooccurrence(sl12_lbl, "statements", sl12_parser, top_n)

    result = {
        "ptbxl": {"labels": ptbxl_labels, "matrix": ptbxl_matrix},
        "12sl":  {"labels": sl12_labels,  "matrix": sl12_matrix},
    }
    write_json(result, out / "label_cooccurrence.json")


def compute_snomed_coverage(ptbxl_lbl, sl12_lbl, snomed_df, out: Path):
    total_snomed = len(snomed_df)

    ptbxl_snomed = set()
    for val in ptbxl_lbl["scp_codes_ext_snomed"].dropna():
        for sid, _ in safe_parse(val):
            ptbxl_snomed.add(int(sid))

    sl12_snomed = set()
    for val in sl12_lbl["statements_ext_snomed"].dropna():
        for sid, _ in safe_parse(val):
            sl12_snomed.add(int(sid))

    result = {
        "total_in_description": total_snomed,
        "ptbxl_unique": len(ptbxl_snomed),
        "12sl_unique":  len(sl12_snomed),
        "both_unique":  len(ptbxl_snomed & sl12_snomed),
        "ptbxl_only":   len(ptbxl_snomed - sl12_snomed),
        "12sl_only":    len(sl12_snomed - ptbxl_snomed),
        "ptbxl_pct_of_desc": round(len(ptbxl_snomed) / total_snomed * 100, 1),
        "12sl_pct_of_desc":  round(len(sl12_snomed)  / total_snomed * 100, 1),
    }
    write_json(result, out / "snomed_coverage.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7 — Fiducial point coverage
# ─────────────────────────────────────────────────────────────────────────────

def compute_fiducial_coverage(fid_dir: Path, fid_ids, records_list, out: Path):
    all_leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    lead_counts = {lead: 0 for lead in all_leads}

    # Count per-lead .atr files
    for sub in fid_dir.iterdir():
        if sub.is_dir():
            for lead in all_leads:
                lead_str = lead.replace("aV", "aV")
                count = len(list(sub.glob(f"*_points_lead_{lead}.atr")))
                lead_counts[lead] += count

    # Sample annotation types from one record
    sample_types = []
    try:
        import wfdb
        sample_file = fid_dir / "00000" / "00001_points_lead_I"
        ann = wfdb.rdann(str(sample_file), "atr")
        sample_types = list(set(ann.aux_note))
    except Exception:
        pass

    # Missing from canonical
    canonical_ints = set()
    for r in records_list:
        try:
            canonical_ints.add(int(Path(r).stem.replace("_medians", "")))
        except ValueError:
            pass

    fid_ints = {int(r) for r in fid_ids}
    missing_count = len(canonical_ints - fid_ints)

    result = {
        "total_with_global_atr": len(fid_ids),
        "per_lead_counts": lead_counts,
        "annotation_types_sample": sorted(sample_types),
        "missing_from_canonical": missing_count,
    }
    write_json(result, out / "fiducial_coverage.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8 — Median beat coverage
# ─────────────────────────────────────────────────────────────────────────────

def compute_median_beat_coverage(mb_data, records_list, out: Path):
    canonical_ints = set()
    for r in records_list:
        try:
            canonical_ints.add(int(Path(r).stem.replace("_medians", "")))
        except ValueError:
            pass

    result = {}
    for src, info in mb_data.items():
        mb_dir = info["dir"]
        record_ids = info["records"]

        # Read a sample header
        leads, fs, sig_len = [], None, None
        try:
            sample_recs = sorted(list(record_ids))[:1]
            if sample_recs:
                rid = sample_recs[0]
                # find the .hea file
                hea_files = list(mb_dir.rglob(f"{rid}_medians.hea"))
                if hea_files:
                    with open(hea_files[0]) as f:
                        lines = f.read().splitlines()
                    # first line: name n_sig fs sig_len
                    parts = lines[0].split()
                    fs = int(parts[2]) if len(parts) > 2 else None
                    sig_len = int(parts[3]) if len(parts) > 3 else None
                    for line in lines[1:]:
                        toks = line.split()
                        if len(toks) >= 9:
                            leads.append(toks[-1])
        except Exception as e:
            pass

        ids_int = set()
        for r in record_ids:
            try:
                ids_int.add(int(r))
            except ValueError:
                pass

        missing_count = len(canonical_ints - ids_int)

        result[src] = {
            "record_count": len(record_ids),
            "leads": leads,
            "sampling_rate_hz": fs,
            "signal_length_samples": sig_len,
            "duration_ms": round(sig_len / fs * 1000, 1) if (fs and sig_len) else None,
            "missing_from_canonical": missing_count,
        }

    write_json(result, out / "median_beat_coverage.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9 — Cross-source agreement
# ─────────────────────────────────────────────────────────────────────────────

def compute_cross_source_agreement(ptbxl_lbl, sl12_lbl, snomed_df, out: Path):
    # Map ecg_id → set of SNOMED ids from PTB-XL
    ptbxl_snomed = {}
    for _, row in ptbxl_lbl.iterrows():
        eid = int(row["ecg_id"])
        snomed_ids = set()
        for sid, _ in safe_parse(row["scp_codes_ext_snomed"]):
            snomed_ids.add(int(sid))
        ptbxl_snomed[eid] = snomed_ids

    # Map ecg_id → set of SNOMED ids from 12SL
    sl12_snomed = {}
    for _, row in sl12_lbl.iterrows():
        eid = int(row["ecg_id"])
        snomed_ids = set()
        for sid, _ in safe_parse(row["statements_ext_snomed"]):
            snomed_ids.add(int(sid))
        sl12_snomed[eid] = snomed_ids

    # Per-SNOMED agreement counts
    snomed_counts = defaultdict(lambda: {"ptbxl_only": 0, "12sl_only": 0, "both": 0, "neither": 0})
    common_ids = set(ptbxl_snomed) & set(sl12_snomed)

    for eid in tqdm(common_ids, desc="  cross-source agreement", ncols=80):
        p_ids = ptbxl_snomed[eid]
        s_ids = sl12_snomed[eid]
        for sid in p_ids | s_ids:
            in_p = sid in p_ids
            in_s = sid in s_ids
            if in_p and in_s:
                snomed_counts[sid]["both"] += 1
            elif in_p:
                snomed_counts[sid]["ptbxl_only"] += 1
            else:
                snomed_counts[sid]["12sl_only"] += 1

    # Snomed description lookup
    snomed_lookup = {}
    if "snomed_id" in snomed_df.columns:
        for _, row in snomed_df.iterrows():
            snomed_lookup[int(row["snomed_id"])] = str(row.get("description", ""))

    rows = []
    for sid, counts in snomed_counts.items():
        total = counts["both"] + counts["ptbxl_only"] + counts["12sl_only"]
        if total < 5:
            continue
        rows.append({
            "snomed_id": sid,
            "description": snomed_lookup.get(sid, str(sid)),
            "both": counts["both"],
            "ptbxl_only": counts["ptbxl_only"],
            "12sl_only": counts["12sl_only"],
            "total": total,
            "agreement_pct": round(counts["both"] / total * 100, 1) if total else 0,
        })
    rows.sort(key=lambda x: -x["total"])

    result = {
        "common_records": len(common_ids),
        "top_concepts": rows[:50],
    }
    write_json(result, out / "cross_source_agreement.json")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10 — Generate HTML report
# ─────────────────────────────────────────────────────────────────────────────

def render_report(data_dir: Path, report_path: Path, template_path: Path, d3_path: Path):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)

    d3_src = d3_path.read_text()

    # Load all JSON blobs
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
    parser = argparse.ArgumentParser(description="PTB-XL+ analysis script")
    parser.add_argument("--config", default="analysis/ptbxlplus/config.yaml")
    args = parser.parse_args()

    cfg_path = REPO_ROOT / args.config
    cfg = load_config(cfg_path)

    root = Path(cfg["dataset"]["root"])
    out_dir = REPO_ROOT / cfg["output"]["data_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    report_html = REPO_ROOT / cfg["output"]["report_html"]
    template_path = REPO_ROOT / "scripts" / "report_template_ptbxlplus.html"
    d3_path = REPO_ROOT / "scripts" / "vendor" / "d3.min.js"

    top_n = cfg["analysis"]["top_n_labels"]
    cooc_n = cfg["analysis"]["cooccurrence_top_n"]
    missing_thresh = cfg["analysis"]["missing_threshold_pct"]

    print("\n[Phase 2] Loading data...")
    feat_dfs, desc_df = load_features(root, cfg)
    ptbxl_lbl, sl12_lbl, snomed_df, map_ptbxl, map_12sl = load_labels(root, cfg)
    fid_dir, fid_ids = scan_fiducial(root, cfg)
    mb_data = scan_median_beats(root, cfg)
    records_list = load_records_file(root, cfg)
    print(f"  RECORDS entries: {len(records_list)}")

    print("\n[Phase 3] Dataset summary...")
    compute_summary(feat_dfs, ptbxl_lbl, sl12_lbl, snomed_df,
                    fid_ids, mb_data, records_list, out_dir)

    print("\n[Phase 4] Record coverage...")
    compute_record_coverage(feat_dfs, ptbxl_lbl, sl12_lbl, fid_ids, mb_data, records_list, out_dir)

    print("\n[Phase 5a] Feature missing values...")
    compute_feature_missing(feat_dfs, desc_df, missing_thresh, out_dir)

    print("\n[Phase 5b] Feature summary statistics...")
    compute_feature_stats(feat_dfs, desc_df, out_dir)

    print("\n[Phase 6a] Label frequency...")
    compute_label_freq(ptbxl_lbl, sl12_lbl, snomed_df, top_n, out_dir)

    print("\n[Phase 6b] Label co-occurrence...")
    compute_label_cooccurrence(ptbxl_lbl, sl12_lbl, cooc_n, out_dir)

    print("\n[Phase 6c] SNOMED coverage...")
    compute_snomed_coverage(ptbxl_lbl, sl12_lbl, snomed_df, out_dir)

    print("\n[Phase 7] Fiducial point coverage...")
    compute_fiducial_coverage(fid_dir, fid_ids, records_list, out_dir)

    print("\n[Phase 8] Median beat coverage...")
    compute_median_beat_coverage(mb_data, records_list, out_dir)

    print("\n[Phase 9] Cross-source agreement...")
    compute_cross_source_agreement(ptbxl_lbl, sl12_lbl, snomed_df, out_dir)

    print("\n[Phase 10] Rendering HTML report...")
    render_report(out_dir, report_html, template_path, d3_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
