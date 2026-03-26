# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ECGDatasets is a Python project for working with ECG (electrocardiogram) datasets, intended for machine learning or medical data analysis. The repository is in early development — no source code, dependencies, or build tooling exist yet.

## Repository State

- **License:** Apache 2.0
- **Author:** Vajira Thambawita
- **Remote:** https://github.com/vlbthambawita/ECGDatasets.git

## GitHub Pages

The site lives in `docs/index.html` — a single-file static page (no build step). To enable it on GitHub: go to **Settings → Pages → Source → Deploy from a branch**, select `main` and `/docs`. The live URL will be `https://vlbthambawita.github.io/ECGDatasets/`.

When updating the dataset table, edit both `README.md` and `docs/index.html` to keep them in sync.

## HuggingFace Space

The site is also mirrored at `https://huggingface.co/spaces/vlbthambawita/ECGDatasets` (static HTML Space).

- HF Space metadata lives in `hf_space/README.md` (frontmatter controls Space title, emoji, license, etc.)
- `.github/workflows/deploy-to-hf.yml` auto-deploys `docs/` to the Space on every push to `main`
- Requires a `HF_TOKEN` secret in the GitHub repo (Settings → Secrets → Actions)
- The `HF_SPACE` variable in the workflow must match your actual HuggingFace username/space-name

