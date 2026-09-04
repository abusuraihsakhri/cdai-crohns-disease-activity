# Crohn's Disease Activity Index (CDAI) & Harvey-Bradshaw Index (HBI) Engine

A clinically validated, pure Python clinical research and gastroenterology scoring engine implementing the **Crohn's Disease Activity Index (CDAI)** (Best WR et al., *Gastroenterology* 1976), Harvey-Bradshaw Index (HBI), and standardized clinical trial efficacy endpoints (CR-70, CR-100, Clinical Remission).

---

## The CDAI & HBI Mathematical Formulations

### 1. Best 1976 CDAI Formula & Subcomponent Weights

The CDAI synthesizes a 7-day diary, extra-intestinal complications, physical examination, and laboratory metrics:

$$\text{CDAI} = 2 \cdot S_1 + 5 \cdot S_2 + 7 \cdot S_3 + 20 \cdot S_4 + 30 \cdot S_5 + 10 \cdot S_6 + 6 \cdot S_7 + 1 \cdot S_8$$

| Subscore | Clinical Variable | Multiplier | Calculation |
|:---|:---|:---:|:---|
| **$S_1$** | Number of liquid or soft stools | $\times 2$ | 7-day sum of daily liquid stool counts |
| **$S_2$** | Abdominal pain rating | $\times 5$ | 7-day sum ($0=\text{none}, 1=\text{mild}, 2=\text{moderate}, 3=\text{severe}$; max 21) |
| **$S_3$** | General well-being | $\times 7$ | 7-day sum ($0=\text{well}, 1=\text{under par}, 2=\text{poor}, 3=\text{very poor}, 4=\text{terrible}$; max 28) |
| **$S_4$** | Complications (Extra-intestinal) | $\times 20$ | Count of: arthralgia, mucocutaneous lesions, uveitis, fissures/fistulas/abscesses, other fistula, fever $>37.8^\circ\text{C}$ |
| **$S_5$** | Antidiarrheal drug usage | $\times 30$ | Binary flag: $1$ if taking loperamide/diphenoxylate/opiates for diarrhea; else $0$ |
| **$S_6$** | Abdominal mass | $\times 10$ | $0 = \text{none}, 2 = \text{questionable}, 5 = \text{definite mass}$ |
| **$S_7$** | Hematocrit deviation | $\times 6$ | Standard Hct ($47\%$ for males, $42\%$ for females) minus patient's Hct |
| **$S_8$** | Body weight deviation | $\times 1$ | $(1 - \frac{\text{Actual Weight}}{\text{Standard Weight}}) \times 100$ (capped at $-10\%$ for overweight) |

---

### 2. Clinical Severity Stratification & Trial Response

| CDAI Range | Severity Tier | Clinical Guidance |
|:---|:---|:---|
| **$< 150$** | **Clinical Remission** | Quiescent disease. Maintain maintenance therapy; routine calprotectin monitoring. |
| **$150 - 219$** | **Mildly Active** | Low-grade symptoms. Consider budesonide or therapeutic drug monitoring (TDM). |
| **$220 - 450$** | **Moderately Active** | Significant inflammatory burden. Initiate/escalate advanced biologic therapy. |
| **$> 450$** | **Severely Active / Fulminant** | Urgent hospitalization; rule out perforation/abscess; intravenous corticosteroids. |

- **Clinical Response Endpoints:**
  - **CR-70:** Absolute decrease of $\ge 70\text{ points}$ from baseline.
  - **CR-100:** Absolute decrease of $\ge 100\text{ points}$ from baseline.
  - **Clinical Remission:** Post-treatment CDAI $< 150$.

---

## Features

- **Full CDAI & HBI Implementations:** Rapid bedside HBI calculation and full 7-day diary CDAI scoring.
- **Trial Efficacy Evaluator:** Compares baseline vs. post-treatment scores for regulatory trial endpoints.
- **Batch CSV Processing:** High-throughput processing for clinical registries and drug trial cohorts.
- **Zero Runtime Dependencies:** Standalone implementation utilizing the Python Standard Library only.

---

## Installation & Requirements

- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- Zero external runtime dependencies.

```bash
git clone https://github.com/abusuraihsakhri/cdai-crohns-disease-activity.git
cd cdai-crohns-disease-activity
```

---

## CLI Usage

### 1. Calculate CDAI for a Patient
```bash
python cli.py cdai --stools 14 --pain 7 --wellbeing 10 --hct 38.5 --sex MALE --weight 65 --std-weight 70
```

### 2. Longitudinal Trial Endpoint Comparison
```bash
python cli.py compare --baseline 320 --post 140
```

### 3. Rapid Harvey-Bradshaw Index (HBI)
```bash
python cli.py hbi --wellbeing 2 --pain 1 --stools 4 --mass 1 --arthralgia
```

### 4. Batch Process Cohorts from CSV
```bash
python cli.py batch --input sample.csv --output results.csv
```

---

## Python API Quickstart

```python
from cdai_crohns import calculate_cdai, CDAIInput, BiologicalSex

patient_input = CDAIInput(
    liquid_stools_7day_sum=14,
    abdominal_pain_7day_sum=7,
    wellbeing_7day_sum=10,
    hematocrit=38.5,
    sex=BiologicalSex.MALE,
    actual_weight_kg=65.0,
    standard_weight_kg=70.0
)

result = calculate_cdai(patient_input)
print(f"CDAI Score: {result.score:.1f}")
print(f"Severity: {result.severity.value}")
print(f"In Remission: {result.is_remission}")
```

---

## Testing & Verification

Run the test suite:

```bash
python -m pytest -p no:zarr
```

