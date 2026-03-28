# ECGDatasets

> ### Browse the interactive dataset catalogue at [vajira.info/ECGDatasets](https://vajira.info/ECGDatasets/)

A curated, community-maintained catalogue of publicly available ECG (electrocardiogram) datasets — spanning clinical hospitals, challenge competitions, and research institutions worldwide. Datasets are organised by lead configuration and include key metadata: recording format, patient/record counts, access requirements, geographic origin, and the primary publication.

**Why this exists:** Finding the right ECG dataset for a research project is surprisingly time-consuming. This repository consolidates information scattered across PhysioNet, Zenodo, Figshare, and other repositories into a single, searchable reference.

**What's covered:**
- 24 twelve-lead datasets from PhysioNet
- 15 twelve-lead datasets from other repositories (Zenodo, Figshare, BDSP, Mendeley, etc.)
- 12 two-lead datasets (including exercise stress ECG)
- 10 single-lead datasets
- 2 three-lead datasets
- 1 BSPM / ECGI dataset

**64 datasets total.**

Contributions and corrections are welcome — please open an issue or pull request.

## 12-Lead ECG Datasets

| # | Dataset Name | Link | Format | Patients | Records | Access | Origin | Paper |
|---|-------------|------|--------|----------|---------|--------|--------|-------|
| 1 | PTB-XL | [physionet.org](https://physionet.org/content/ptb-xl/1.0.3/) | 12-lead, 10 s, 500 Hz (also 100 Hz) | 18,869 | 21,799 | Open (CC BY 4.0) | Germany — Physikalisch-Technische Bundesanstalt (PTB) | [PTB-XL: A Large Publicly Available ECG Dataset](https://doi.org/10.1038/s41597-020-0495-6) |
| 2 | PTB-XL+ | [physionet.org](https://physionet.org/content/ptb-xl-plus/1.0.1/) | 12-lead, 10 s, 500 Hz (derived from PTB-XL; adds features, median beats, SNOMED mappings) | 18,869 | 21,799 | Open (CC BY 4.0) | Germany — Karlsruhe Institute of Technology | [PTB-XL+: A Comprehensive Electrocardiographic Feature Dataset](https://doi.org/10.1038/s41597-023-02153-8) |
| 3 | PTB Diagnostic ECG Database | [physionet.org](https://physionet.org/content/ptbdb/1.0.0/) | 15-lead (12 standard + 3 Frank), variable duration, 1,000 Hz | 290 | 549 | Open (ODC Attribution) | Germany — PTB / University Clinic Benjamin Franklin, Berlin | [Bousseljot et al., 1995](https://doi.org/10.13026/C28C71) |
| 4 | MIMIC-IV-ECG | [physionet.org](https://physionet.org/content/mimic-iv-ecg/1.0/) | 12-lead, 10 s, 500 Hz | ~160,000 | ~800,000 | Credentialed (PhysioNet DUA) | USA — Beth Israel Deaconess Medical Center, Boston | [Gow et al.](https://doi.org/10.13026/4nqg-sb35) |
| 5 | MIMIC-IV-ECG Demo | [physionet.org](https://physionet.org/content/mimic-iv-ecg-demo/0.1/) | 12-lead, 10 s, 500 Hz | 92 | 659 | Open | USA — Beth Israel Deaconess Medical Center, Boston | [Dataset DOI](https://doi.org/10.13026/4eqn-kt76) |
| 6 | MIMIC-IV-ECG-Ext-ICD | [physionet.org](https://physionet.org/content/mimic-iv-ecg-ext-icd-labels/1.0.1/) | 12-lead, 10 s, 500 Hz; 1,076 ICD-10-CM codes | Subset of MIMIC-IV-ECG | Subset of MIMIC-IV-ECG | Credentialed | USA/Germany — MIT LCP + collaborators | [Eur Heart J Digital Health, 2024](https://doi.org/10.1093/ehjdh/ztae039) |
| 7 | Chapman-Shaoxing (Arrhythmia) | [physionet.org](https://physionet.org/content/ecg-arrhythmia/1.0.0/) | 12-lead, 10 s, 500 Hz | 45,152 | 45,152 | Open (CC BY 4.0) | China/USA — Chapman University; Shaoxing People's Hospital & Ningbo First Hospital | [Zheng et al., Scientific Reports, 2020](https://doi.org/10.1038/s41598-020-59821-7) |
| 8 | St Petersburg INCART 12-Lead Arrhythmia Database | [physionet.org](https://physionet.org/content/incartdb/1.0.0/) | 12-lead, 30 min, 257 Hz | 32 | 75 | Open | Russia — St. Petersburg Institute of Cardiological Technics (INCART) | [Dataset DOI](https://doi.org/10.13026/C2V88N) |
| 9 | Lobachevsky University ECG Database (LUDB) | [physionet.org](https://physionet.org/content/ludb/1.0.1/) | 12-lead, 10 s, 500 Hz; manually annotated waves | 200 | 200 | Open (ODC Attribution) | Russia — Nizhny Novgorod City Hospital No. 5 / Lobachevsky University | [IEEE Access, 2020](https://doi.org/10.1109/ACCESS.2020.3029211) |
| 10 | Brugada-HUCA | [physionet.org](https://physionet.org/content/brugada-huca/1.0.0/) | 12-lead, 12 s, 100 Hz | 363 (76 Brugada, 287 controls) | 363 | Open (CC BY-SA 4.0) | Spain — Hospital Universitario Central de Asturias (HUCA) | [Dataset DOI](https://doi.org/10.13026/0m2w-dy83) |
| 11 | KURIAS-ECG | [physionet.org](https://physionet.org/content/kurias-ecg/1.0/) | 12-lead, 10 s, 500 Hz; SNOMED CT + OMOP-CDM labels | 13,862 | 20,000 | Restricted (pending audit) | South Korea — Korea University Anam Hospital, Seoul | [Dataset DOI](https://doi.org/10.13026/kga0-0270) |
| 12 | Leipzig Heart Center ECG Database | [physionet.org](https://physionet.org/content/leipzig-heart-center-ecg/1.0.0/) | 12-lead + intracardiac electrograms, variable duration, 977 Hz | 39 | 39 | Open (ODC Attribution) | Germany — Leipzig Heart Center | [Dataset DOI](https://doi.org/10.13026/7a4j-vn37) |
| 13 | Norwegian Endurance Athlete ECG Database | [physionet.org](https://physionet.org/content/norwegian-athlete-ecg/1.0.0/) | 12-lead, 10 s, 500 Hz | 28 | 28 | Open (CC BY 4.0) | Norway — University of Oslo | [Dataset DOI](https://doi.org/10.13026/qpjf-gk87) |
| 14 | MHD Effect on 12-Lead ECGs in MRI Scanners | [physionet.org](https://physionet.org/content/mhd-effect-ecg-mri/1.0.0/) | 12-lead and 3-lead, variable duration, 1,024 Hz | 23 | 43 | Open | Germany — Otto-von-Guericke University of Magdeburg | [Krug et al., CinC 2017](https://doi.org/10.13026/05td-jn37) |
| 15 | Wilson Central Terminal ECG Database | [physionet.org](https://physionet.org/content/wctecgdb/1.0.1/) | 37 signals (12 standard leads + Wilson Central Terminal + limb potentials), 10 s | 92 | 540 | Open (ODC Attribution) | Australia — MARCS Institute, Western Sydney University; Campbelltown Hospital | [Machines, 2016](https://doi.org/10.3390/machines4040018) |
| 16 | CiPA ECG Validation Study | [physionet.org](https://physionet.org/content/ecgcipa/1.0.0/) | 12-lead, 10 s | 60 | 5,749 segments | Open (ODC Attribution) | USA — Phase I clinical pharmacology study (NCT03070470) | [Clin Pharmacol Ther, 2018](https://doi.org/10.1002/cpt.1303) |
| 17 | ECG Effects of Dofetilide, Moxifloxacin and Combinations (ECGDMMLD) | [physionet.org](https://physionet.org/content/ecgdmmld/1.0.0/) | 12-lead, 10 s, 500 Hz (upsampled to 1,000 Hz) | 22 | 4,211 segments | Open (ODC Attribution) | USA (NCT02308748) | [Clin Pharmacol Ther, 2016](https://doi.org/10.1002/cpt.205) |
| 18 | ECG Effects of Ranolazine, Dofetilide, Verapamil, Quinidine (ECGRDVQ) | [physionet.org](https://physionet.org/content/ecgrdvq/1.0.0/) | 12-lead, 10 s, 500 Hz | 22 | 5,232 segments | Open (ODC Attribution) | USA | [Clin Pharmacol Ther, 2014](https://doi.org/10.1038/clpt.2014.155) |
| 19 | Eye Tracking Dataset for 12-Lead ECG Interpretation | [physionet.org](https://physionet.org/content/eye-tracking-ecg/1.0.0/) | 12-lead ECG images; eye tracking at 60 Hz | 63 (interpreters) | 630 sessions | Open (ODC ODbL) | Qatar — Qatar Biomedical Research Institute, Hamad bin Khalifa University | [JMIR, 2022](http://dx.doi.org/10.2196/34058) |
| 20 | EchoNext | [physionet.org](https://physionet.org/content/echonext/1.1.0/) | 12-lead, 10 s, 250 Hz | Not disclosed | 100,000 | Restricted | USA — Columbia University Irving Medical Center, New York | Poterucha et al., Nature, 2025 |
| 21 | Symile-MIMIC | [physionet.org](https://physionet.org/content/symile-mimic/1.0.0/) | 12-lead, 10 s, 500 Hz (multimodal: ECG + CXR + labs) | 9,573 | 11,622 | Credentialed | USA — MIT LCP / BIDMC | [NeurIPS 2024](https://doi.org/10.13026/3vvj-s428) |
| 22 | PhysioNet/CinC Challenge 2020 | [physionet.org](https://physionet.org/content/challenge-2020/1.0.2/) | 12-lead, 6–60 s, 257–1,000 Hz | — | ~52,501 | Open (CC BY 4.0) | Multi-national (China, Russia, Germany, USA) | [Physiol Meas, 2020](https://doi.org/10.1088/1361-6579/abc960) |
| 23 | PhysioNet/CinC Challenge 2021 | [physionet.org](https://physionet.org/content/challenge-2021/1.0.3/) | 12-lead (+ reduced-lead versions), 5–144 s, 250–1,000 Hz | — | ~130,862 | Open (CC BY 4.0) | Multi-national (China, Russia, Germany, USA) | [CinC 2021](https://doi.org/10.23919/CinC53138.2021.9662687) |
| 24 | STAFF III Database | [physionet.org](https://physionet.org/content/staffiii/1.0.0/) | 12-lead, variable duration, 1,000 Hz, 0.625 µV resolution; PTCA-induced ischemia | 104 | 152 inflations | Open (ODC Attribution) | USA — Charleston Area Medical Center, WV; Blekinge Hospital, Sweden | [Martínez et al., CinC 2017](https://doi.org/10.22489/CinC.2017.266-133) |

## 12-Lead ECG Datasets (Other Repositories)

| # | Dataset Name | Link | Format | Patients | Records | Access | Origin | Paper |
|---|-------------|------|--------|----------|---------|--------|--------|-------|
| 1 | CPSC 2018 (China Physiological Signal Challenge 2018) | [icbeb.org](http://2018.icbeb.org/Challenge.html) | 12-lead, 6–60 s, 500 Hz, MATLAB .mat | ~6,877 | 6,877 | Open | China — 11 hospitals (ICBEB, Nanjing) | [Liu et al., J. Med. Imaging Health Inform. 2018](https://doi.org/10.1166/jmihi.2018.2442) |
| 2 | Chapman-Shaoxing ECG Database (10,646 patients) | [figshare.com](https://doi.org/10.6084/m9.figshare.c.4560497.v2) | 12-lead, 10 s, 500 Hz, CSV | 10,646 | 10,646 | Open (CC BY 4.0) | China/USA — Chapman University; Shaoxing People's Hospital | [Zheng et al., Scientific Data, 2020](https://doi.org/10.1038/s41597-020-0386-x) |
| 3 | Ningbo First Hospital ECG Database (Idiopathic Ventricular Arrhythmia) | [figshare.com](https://doi.org/10.6084/m9.figshare.c.4668086.v2) | 12-lead, 10 s, 500 Hz, CSV | 334 | 334 | Open (CC BY 4.0) | China/USA — Chapman University; Ningbo First Hospital, Zhejiang University | [Zheng et al., Scientific Data, 2020](https://doi.org/10.1038/s41597-020-0440-8) |
| 4 | Shandong Provincial Hospital ECG Database (SPHDB) | [figshare.com](https://doi.org/10.6084/m9.figshare.c.5779802.v1) | 12-lead, 10–60 s, 500 Hz, HDF5 | 24,666 | 25,770 | Open (CC BY 4.0) | China — Shandong Provincial Hospital | [Liu et al., Scientific Data, 2022](https://doi.org/10.1038/s41597-022-01403-5) |
| 5 | CODE-15% (Telehealth Network of Minas Gerais, 15% subset) | [zenodo.org](https://doi.org/10.5281/zenodo.4916206) | 12-lead, ~10 s, 400 Hz, HDF5 | 233,770 | 345,779 | Open (CC BY 4.0) | Brazil — Telehealth Network of Minas Gerais (TNMG) | [Ribeiro et al., Nature Communications, 2020](https://doi.org/10.1038/s41467-020-15432-4) |
| 6 | CODE-test (827-record hold-out test set) | [zenodo.org](https://doi.org/10.5281/zenodo.3765780) | 12-lead, 7–10 s, 400 Hz, HDF5 | 827 | 827 | Open (CC BY 4.0) | Brazil — Universidade Federal de Minas Gerais / TNMG | [Ribeiro et al., Nature Communications, 2020](https://doi.org/10.1038/s41467-020-15432-4) |
| 7 | CODE (Full Dataset, ~2.3M records) | [figshare.scilifelab.se](https://figshare.scilifelab.se/articles/dataset/CODE_dataset/15169716) | 12-lead, 400 Hz, HDF5 | ~1,676,384 | ~2,322,513 | Restricted (DUA required) | Brazil — TNMG, 811 municipalities in Minas Gerais | [Ribeiro et al., Nature Communications, 2020](https://doi.org/10.1038/s41467-020-15432-4) |
| 8 | SaMi-Trop (Chagas cardiomyopathy cohort) | [zenodo.org](https://doi.org/10.5281/zenodo.4905618) | 12-lead, 400 Hz, HDF5 | 1,631 | 1,631 | Open (CC BY 4.0) | Brazil — Universidade Federal de Minas Gerais; Uppsala University; EPFL | [Lima et al., medRxiv, 2021](https://doi.org/10.1101/2021.02.19.21251232) |
| 9 | IKEM Dataset (Institute for Clinical and Experimental Medicine, Prague) | [zenodo.org](https://doi.org/10.5281/zenodo.8393007) | 12-lead (stored as 8 reduced leads), 10 s, 500 Hz, HDF5 | 30,290 | 98,130 | Open (CC BY 4.0) | Czech Republic — IKEM, Prague | [Seják et al., Knowledge-Based Systems, 2023](https://doi.org/10.1016/j.knosys.2023.111014) |
| 10 | MedalCare-XL (Synthetic 12-Lead ECGs) | [zenodo.org](https://doi.org/10.5281/zenodo.8068944) | 12-lead, 10 s, 500 Hz, CSV (raw/noise-added/filtered variants) | 0 (synthetic) | 16,900 | Open (CC BY 4.0) | Austria/Germany/UK — Medical Univ. of Graz, KIT, PTB, Univ. of Edinburgh | [Gillette et al., Scientific Data, 2023](https://doi.org/10.1038/s41597-023-02416-4) |
| 11 | Harvard-Emory ECG Database (HEEDB) | [bdsp.io](https://bdsp.io/content/heedb/5.0/) | 12-lead, 10 s, 250/500 Hz, WFDB | 2,167,795 | 11,607,261 | Credentialed (DUA, BDSP platform) | USA — Massachusetts General Hospital; Emory University Hospital | [Koscova et al., Scientific Data, 2026](https://doi.org/10.1038/s41597-026-06861-9) |
| 12 | Nightingale BWH Emergency Dept ECG Dataset | [ngsci.org](https://docs.ngsci.org/datasets/ed-bwh-ecg/) | 12-lead, 100 Hz, NumPy arrays | 30,933 | 103,952 | Restricted (institutional credentials) | USA — Brigham and Women's Hospital, Boston | [Mullainathan & Obermeyer, QJE, 2021](https://doi.org/10.1093/qje/qjab046) |
| 13 | Nightingale NTUH Cardiac Arrest ECG Dataset | [ngsci.org](https://docs.ngsci.org/datasets/arrest-ntuh-ecg/) | 12-lead, ~500 Hz, XML/array | 10,950 | 18,072 | Restricted (institutional credentials) | Taiwan — National Taiwan University Hospital, Emergency Dept | [Obermeyer et al., Nature Medicine, 2022](https://doi.org/10.1038/s41591-022-01804-4) |
| 14 | GU-ECG (Gazi University, PTCA-induced Ischaemia) | [mendeley.com](https://doi.org/10.17632/zhr5zsngtg.1) | 12-lead continuous, 8,800 Hz, 24-bit, .ekg format | 74 | 222 | Open (CC BY 4.0) | Turkey — Gazi University Faculty of Medicine; Bilkent University | [Dataset DOI](https://doi.org/10.17632/zhr5zsngtg.1) |
| 15 | ZZU pECG (Zhengzhou University Pediatric ECG Database) | [figshare.com](https://doi.org/10.6084/m9.figshare.27078763) | 12-lead + 9-lead, 5–120 s, 500 Hz, WFDB | 11,643 children | 14,190 | Open | China — First Affiliated Hospital of Zhengzhou University | [Scientific Data, 2025](https://doi.org/10.1038/s41597-025-05225-z) |

## 1-Lead ECG Datasets

| # | Dataset Name | Link | Format | Patients | Records | Access | Origin | Paper |
|---|-------------|------|--------|----------|---------|--------|--------|-------|
| 1 | Icentia11k Single Lead Continuous ECG | [physionet.org](https://physionet.org/content/icentia11k-continuous-ecg/1.0/) | 1-lead (modified Lead I), ~70 min segments, 250 Hz | 11,000 | 541,794 segments | Open (CC BY-NC-SA 4.0) | Canada — Université de Montréal; Icentia Inc. | [Tan et al., CinC 2021](https://arxiv.org/abs/1910.09570) |
| 2 | PhysioNet/CinC Challenge 2017 (AF Classification) | [physionet.org](https://physionet.org/content/challenge-2017/1.0.0/) | 1-lead (AliveCor device), 9–61 s, 300 Hz | — | 12,186 | Open (training set; ODC Attribution) | USA — AliveCor Inc. / MIT-Harvard PhysioNet | [Clifford et al., CinC 2017](https://doi.org/10.22489/CinC.2017.065-469) |
| 3 | Apnea-ECG Database | [physionet.org](https://physionet.org/content/apnea-ecg/1.0.0/) | 1-lead, 7–10 h overnight, 100 Hz | ~70 | 70 | Open (ODC Attribution) | Germany — Philipps-University Marburg | [Penzel et al., CinC 2000](https://doi.org/10.13026/C23W2R) |
| 4 | ECG-ID Database | [physionet.org](https://physionet.org/content/ecgiddb/1.0.0/) | 1-lead (Lead I, wrist), 20 s, 500 Hz | 90 | 310 | Open (ODC Attribution) | Russia — Electrotechnical University "LETI", St. Petersburg | [Lugovaya, MSc thesis 2005](https://doi.org/10.13026/C2J01F) |
| 5 | Post-Ictal Heart Rate Oscillations in Partial Epilepsy | [physionet.org](https://physionet.org/content/szdb/1.0.0/) | 1-lead, overnight continuous, 200 Hz | 5 | 7 | Open (ODC Attribution) | USA — Beth Israel Deaconess Medical Center / Harvard | [Al-Aweel et al., Neurology 1999](https://doi.org/10.13026/C2QC72) |
| 6 | tOLIet (Thigh-based ECG, toilet seat) | [physionet.org](https://physionet.org/content/tollet/1.0.1/) | 1-lead (thigh, dry polymer electrodes), up to 5 min, 1,000 Hz | 86 | 149 | Open (CC BY 4.0) | Portugal — Centro Hospitalar Universitário de Lisboa Central (CHULC) | [Silva et al., Scientific Data 2026](https://doi.org/10.1038/s41597-026-06713-6) |
| 7 | Brno University of Technology ECG Quality Database (BUT QDB) | [physionet.org](https://physionet.org/content/butqdb/1.0.0/) | 1-lead (Bittium Faros 180 wearable) + 3-axis accel., ≥24 h, 1,000 Hz | 15 | 18 | Open (CC BY 4.0) | Czech Republic — Brno University of Technology | [Smital et al., IEEE TBME 2020](https://doi.org/10.1109/tbme.2020.2969719) |
| 8 | VitalDB Arrhythmia Database | [physionet.org](https://physionet.org/content/vitaldb-arrhythmia/1.0.0/) | 1-lead (Lead II, intraoperative), ~20 min median, 500 Hz | 482 | 482 | Open (CC BY 4.0) | South Korea — Seoul National University Hospital | [Eun et al., Scientific Data 2026](https://doi.org/10.1038/s41597-026-07076-8) |
| 9 | Preterm Infant Cardio-Respiratory Signals Database (PICSDB) | [physionet.org](https://physionet.org/content/picsdb/1.0.0/) | 1-lead (single channel from bedside monitor), 20–70 h, 500 Hz | 10 infants | 10 | Open (ODC Attribution) | USA — UMass Memorial Healthcare NICU, Worcester | [Shamout et al., IEEE TBME 2017](https://doi.org/10.1109/TBME.2016.2632746) |
| 10 | ECG-Capable Smartwatches Dataset | [physionet.org](https://physionet.org/content/ecg-capable-smartwatches/1.0.0/) | 1-lead (Lead I), 10 s (4 smartwatch models + reference device, synthetic signals) | 0 (synthetic) | 915 | Restricted (DUA required) | Spain — Instituto Ramón y Cajal de Investigación Sanitaria | Recas et al. (pending) |

## 2-Lead ECG Datasets

| # | Dataset Name | Link | Format | Patients | Records | Access | Origin | Paper |
|---|-------------|------|--------|----------|---------|--------|--------|-------|
| 1 | MIT-BIH Arrhythmia Database | [physionet.org](https://physionet.org/content/mitdb/1.0.0/) | 2-lead (MLII + V1), 30 min, 360 Hz, WFDB | 47 | 48 | Open (ODC Attribution) | USA — Beth Israel Hospital / MIT | [Moody & Mark, IEEE EMBS 2001](https://doi.org/10.13026/C2F305) |
| 2 | MIT-BIH Atrial Fibrillation Database | [physionet.org](https://physionet.org/content/afdb/1.0.0/) | 2-lead, 10 h, 250 Hz, WFDB | 25 | 25 | Open (ODC Attribution) | USA — Beth Israel Hospital | [Moody & Mark, CinC 1983](https://doi.org/10.13026/C2MW2D) |
| 3 | Long-Term AF Database (LTAFDB) | [physionet.org](https://physionet.org/content/ltafdb/1.0.0/) | 2-lead, 24–25 h, 128 Hz, WFDB | 84 | 84 | Open (ODC Attribution) | USA/Poland — Northwestern University; MEDICALgorithmics | [Petrutiu et al., Europace 2007](https://doi.org/10.13026/C2QG6Q) |
| 4 | MIT-BIH Normal Sinus Rhythm Database | [physionet.org](https://physionet.org/content/nsrdb/1.0.0/) | 2-lead, ~24 h, 128 Hz, WFDB | 18 | 18 | Open (ODC Attribution) | USA — Beth Israel Hospital | [Dataset DOI](https://doi.org/10.13026/C2NK5R) |
| 5 | MIT-BIH Supraventricular Arrhythmia Database | [physionet.org](https://physionet.org/content/svdb/1.0.0/) | 2-lead (MLII + V1), 30 min, 360 Hz, WFDB | — | 78 | Open (ODC Attribution) | USA — MIT / Harvard-MIT HST | [Greenwald, PhD thesis, Harvard-MIT 1990](https://doi.org/10.13026/C2V30W) |
| 6 | European ST-T Database (EDB) | [physionet.org](https://physionet.org/content/edb/1.0.0/) | 2-lead ambulatory, 2 h, 250 Hz, WFDB | 79 | 90 | Open (ODC Attribution) | Italy — CNR Institute for Clinical Physiology, Pisa; European Society of Cardiology | [Taddei et al., Eur Heart J 1992](https://doi.org/10.13026/C2D59Z) |
| 7 | BIDMC Congestive Heart Failure Database | [physionet.org](https://physionet.org/content/chfdb/1.0.0/) | 2-lead, ~20 h, 250 Hz, WFDB | 15 | 15 | Open (ODC Attribution) | USA — Beth Israel Deaconess Medical Center | [Baim et al., J Am Coll Cardiol 1986](https://doi.org/10.13026/C29G60) |
| 8 | Sudden Cardiac Death Holter Database | [physionet.org](https://physionet.org/content/sddb/1.0.0/) | 2-lead, 4–25 h, 250 Hz, WFDB | 23 | 23 | Open (ODC Attribution) | USA — MIT | [Greenwald, MS thesis, MIT 1986](https://doi.org/10.13026/C2W306) |
| 9 | QT Database (QTDB) | [physionet.org](https://physionet.org/content/qtdb/1.0.0/) | 2-lead, 15 min, various Hz, WFDB | — | 105 | Open (ODC Attribution) | USA — MIT / PhysioNet | [Laguna et al., CinC 1997](https://doi.org/10.13026/C24K53) |
| 10 | SHDB-AF (Saitama Holter Database — Atrial Fibrillation) | [physionet.org](https://physionet.org/content/shdb-af/1.0.1/) | 2-lead (CC5 + NASA), ~24 h, 125 Hz, WFDB | 122 | 128 | Open (ODC Attribution) | Japan — Saitama Medical University International Medical Center | [Tsutsui et al., Scientific Data 2025](https://doi.org/10.13026/n6yq-fq90) |
| 11 | MIT-BIH ST Change Database | [physionet.org](https://physionet.org/content/stdb/1.0.0/) | 2-lead, variable length, 360 Hz, WFDB; mostly exercise stress test ECGs with transient ST depression/elevation | — | 28 | Open (ODC Attribution) | USA — MIT / PhysioNet | [Dataset DOI](https://doi.org/10.13026/C2ZW2H) |
| 12 | Long-Term ST Database (LTSTDB) | [physionet.org](https://physionet.org/content/ltstdb/1.0.0/) | 2–3 lead, 21–24 h, 250 Hz, WFDB; annotated ST episodes (ischemic, axis-related, drift) | 80 | 86 | Open (ODC Attribution) | Multi-national (EU) — Ljubljana, Pisa, Cambridge | [Jager et al., Med Biol Eng Comput, 2003](https://doi.org/10.13026/C2CC7C) |

## 3-Lead ECG Datasets

| # | Dataset Name | Link | Format | Patients | Records | Access | Origin | Paper |
|---|-------------|------|--------|----------|---------|--------|--------|-------|
| 1 | St. Vincent's / UCD Sleep Apnea Database (UCDDB) | [physionet.org](https://physionet.org/content/ucddb/1.0.0/) | 3-lead Holter (V5, CC5, V5R), overnight PSG, 128 Hz, EDF | 25 | 25 | Open (ODC Attribution) | Ireland — St. Vincent's University Hospital / University College Dublin | [Dataset DOI](https://doi.org/10.13026/C26C7D) |
| 2 | MIMIC-III Waveform Database Matched Subset | [physionet.org](https://physionet.org/content/mimic3wdb-matched/1.0/) | 1–5 ECG leads, typically 3-lead ICU monitoring (Lead II, V, AVR), continuous, 125 Hz, WFDB | 10,282 | 22,317 | Open (ODbL) | USA — Beth Israel Deaconess Medical Center, Boston | [Johnson et al., Scientific Data, 2016](https://doi.org/10.1038/sdata.2016.35) |

## BSPM / ECGI Datasets

Body Surface Potential Mapping (BSPM) and Electrocardiographic Imaging (ECGI) datasets use 32–252+ electrodes distributed across the torso to reconstruct 3D cardiac electrical activity.

| # | Dataset Name | Link | Format | Subjects | Records | Access | Origin | Paper |
|---|-------------|------|--------|----------|---------|--------|--------|-------|
| 1 | EDGAR (Experimental Data and Geometric Analysis Repository) | [ecg-imaging.org](https://www.ecg-imaging.org/edgar-database) | BSPM (64+ leads) + endocardial/epicardial data + torso geometry + CT; human, canine, and simulation data; MATLAB/SCIRun format | Multiple (human + animal + simulation) | Multiple datasets | Open (free registration) | Multi-national — University of Utah (USA); Charles University Hospital (Czech Republic); Karlsruhe Institute of Technology (Germany) | [Aras et al., J Electrocardiol, 2015](https://doi.org/10.1016/j.jelectrocard.2015.08.008) |

> **Access types:**
> - **Open** — freely downloadable, no registration required (or only basic PhysioNet account)
> - **Credentialed** — requires PhysioNet credentialing and signing a Data Use Agreement (DUA)
> - **Restricted** — currently unavailable pending review or additional process
