# CDAI Crohns Disease Activity

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Crohn's Disease Activity Index (CDAI) & Harvey-Bradshaw Index (HBI) Engine
==========================================================================
A precision clinical calculator and trial evaluation engine for Crohn's Disease
activity scoring, longitudinal flare tracking, and therapeutic response metrics.

References:
- Best WR, Becktel JM, Singleton JW, Kern F Jr. Development of a Crohn's
  disease activity index. National Cooperative Crohn's Disease Study.
  Gastroenterology. 1976;70(3):439-444.
- Best WR. Predicting the Crohn's disease activity index from the Harvey-Bradshaw Index.
  Inflamm Bowel Dis. 2006;12(4):304-310.
- Harvey RF, Bradshaw JM. A simple index of Crohn's-disease activity.
  Lancet. 1980;1(8167):514.
- Sandborn WJ, Feagan BG, Hanauer SB, et al. A review of activity indices and
  efficacy endpoints for clinical trials of medical therapy in adults with Crohn's
  disease. Gastroenterology. 2002;122(2):512-530.

Author: Clinical AI & Domain Engineering
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`BiologicalSex`** — dedicated module for biological sex evaluation and state verification.
- **`AbdominalMass`** — dedicated module for abdominal mass evaluation and state verification.
- **`CDAISeverity`** — dedicated module for c d a i severity evaluation and state verification.
- **`HBISeverity`** — dedicated module for h b i severity evaluation and state verification.
- **`CDAIComplications`**: Extra-intestinal manifestations and complications (1 point each if present).
- **`CDAIInput`**: Input parameters for CDAI computation over 7-day diary + clinical exam.

---

## 📐 Mathematical Formulation & Logic

```text
  total_score = (
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --stools <value> --pain <value> --wellbeing <value> --hct <value>
```

### Parameter Reference
- `--stools`: Specifies input measurement or parameter value.
- `--pain`: Specifies input measurement or parameter value.
- `--wellbeing`: Specifies input measurement or parameter value.
- `--hct`: Specifies input measurement or parameter value.
- `--sex`: Specifies input measurement or parameter value.
- `--weight`: Specifies input measurement or parameter value.
- `--std-weight`: Specifies input measurement or parameter value.
- `--mass`: Specifies input measurement or parameter value.
- `--arthralgia`: Specifies input measurement or parameter value.
- `--baseline`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t cdai-crohns-disease-activity .
docker run -p 8000:8000 cdai-crohns-disease-activity
```
