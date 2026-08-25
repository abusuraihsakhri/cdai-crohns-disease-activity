# Crohn's Disease Activity Index (CDAI) & Harvey-Bradshaw Index (HBI) Engine

A clinical calculation engine and trial endpoint evaluator for **Crohn's Disease Activity Index (CDAI)** and **Harvey-Bradshaw Index (HBI)**, implementing the exact regression equations and clinical trial efficacy endpoints (CR-70, CR-100, Clinical Remission) from the National Cooperative Crohn's Disease Study.

---

## Clinical Domain & Mathematical Specification

The **Crohn's Disease Activity Index (CDAI)**, developed by Best et al. (1976), is the historical gold standard clinical trial metric for quantifying disease severity and evaluating therapeutic response in Crohn's disease.

### 1. CDAI 8 Subcomponents & Exact Weighting Multipliers

$$\text{CDAI} = (2 \cdot x_1) + (5 \cdot x_2) + (7 \cdot x_3) + (20 \cdot x_4) + (30 \cdot x_5) + (10 \cdot x_6) + (6 \cdot x_7) + (1 \cdot x_8)$$

| Variable | Clinical Parameter | Evaluation Method / Scale | Multiplier | Range / Typical Sub-score |
| :--- | :--- | :--- | :--- | :--- |
| $x_1$ | **Liquid / Soft Stools** | Sum of daily count of liquid or very soft stools over 7 days | $\times 2$ | $0 - 70+$ |
| $x_2$ | **Abdominal Pain** | Sum of daily ratings over 7 days (0=None, 1=Mild, 2=Moderate, 3=Severe) | $\times 5$ | $0 - 21$ (Score: $0 - 105$) |
| $x_3$ | **General Well-Being** | Sum of daily ratings over 7 days (0=Well, 1=Slightly below par, 2=Poor, 3=Very poor, 4=Terrible) | $\times 7$ | $0 - 28$ (Score: $0 - 196$) |
| $x_4$ | **Extra-intestinal Complications** | Count of positive categories present (Arthralgia, Mucocutaneous lesions, Uveitis, Perianal disease, Fistula, Fever $>37.8^\circ\text{C}$) | $\times 20$ | $0 - 6$ (Score: $0 - 120$) |
| $x_5$ | **Anti-diarrheal Use** | Use of diphenoxylate, loperamide, or opiates for diarrhea ($0=\text{No}, 1=\text{Yes}$) | $\times 30$ | $0$ or $30$ |
| $x_6$ | **Abdominal Mass** | $0=\text{None}, 2=\text{Questionable/Equivocal}, 5=\text{Definite Mass}$ | $\times 10$ | $0, 20,$ or $50$ |
| $x_7$ | **Hematocrit Deficit** | $\text{Standard Hct} - \text{Patient Hct}$ ($\text{Std: Male}=47\%, \text{Female}=42\%$) | $\times 6$ | Variable (Signed) |
| $x_8$ | **Body Weight Deviation** | $\left(1 - \frac{\text{Actual Weight}}{\text{Standard Weight}}\right) \times 100$ (overweight contribution clamped at $-10\%$) | $\times 1$ | Variable |

---

### 2. Clinical Severity Tiers & Cutoffs

- **Clinical Remission**: $\text{CDAI} < 150$ (Quiescent disease; maintenance therapy).
- **Mildly Active Crohn's**: $150 \le \text{CDAI} < 220$ (Outpatient management; budesonide/5-ASA).
- **Moderately Active Crohn's**: $220 \le \text{CDAI} \le 450$ (Advanced therapy escalation; biologics/small molecules).
- **Severely Active / Fulminant Crohn's**: $\text{CDAI} > 450$ (Inpatient admission; IV steroids, surgery eval).

---

### 3. Clinical Trial Efficacy Endpoints

- **Clinical Response 70 (CR-70)**: Decrease in CDAI $\ge 70$ points from baseline.
- **Clinical Response 100 (CR-100)**: Decrease in CDAI $\ge 100$ points from baseline.
- **Clinical Remission**: Post-treatment CDAI $< 150$.

---

### 4. Simplified Harvey-Bradshaw Index (HBI)

The **Harvey-Bradshaw Index** (Harvey & Bradshaw, 1980) provides a single-day clinical assessment:
- **$\text{HBI} < 5$**: Clinical Remission
- **$\text{HBI } 5 - 7$**: Mildly Active Disease
- **$\text{HBI } 8 - 16$**: Moderately Active Disease
- **$\text{HBI} > 16$**: Severely Active Disease

---

## Installation & Requirements

Pure Python 3.9+ with zero external dependencies.

```bash
cd cdai-crohns-disease-activity
```

---

## CLI Usage

### 1. Calculate 7-Day CDAI Score
```bash
python cli.py cdai --stools 14 --pain 7 --wellbeing 10 --hct 38.5 --sex MALE --weight 65 --std-weight 70
```

### 2. Output Machine-Readable JSON
```bash
python cli.py cdai --stools 14 --pain 7 --wellbeing 10 --hct 38.5 --sex MALE --weight 65 --std-weight 70 --json
```

### 3. Calculate 1-Day Harvey-Bradshaw Index (HBI)
```bash
python cli.py hbi --wellbeing 2 --pain 1 --stools 4 --mass 1 --arthralgia --skin-lesions
```

### 4. Longitudinal Trial Endpoint Comparison (CR-70 / CR-100 / Remission)
```bash
python cli.py compare --baseline 340 --post 135
```

### 5. Interactive Clinical Assessment Wizard
```bash
python cli.py interactive
```

### 6. Batch Process Cohort CSV File
```bash
python cli.py batch --input patients.csv --output results.csv
```

---

## Python API Usage

```python
from cdai_crohns import CDAIInput, CDAIComplications, AbdominalMass, BiologicalSex, calculate_cdai

complications = CDAIComplications(
    arthritis_or_arthralgia=True,
    anal_fissure_fistula_abscess=True
)

patient_input = CDAIInput(
    liquid_stools_7day_sum=21,
    abdominal_pain_7day_sum=10,
    wellbeing_7day_sum=12,
    complications=complications,
    taking_antidiarrheals=True,
    abdominal_mass=AbdominalMass.QUESTIONABLE,
    hematocrit=36.5,
    sex=BiologicalSex.MALE,
    actual_weight_kg=62.0,
    standard_weight_kg=70.0
)

result = calculate_cdai(patient_input)
print(f"CDAI Score: {result.score:.1f} ({result.severity.value})")
print(f"Is in Remission: {result.is_remission}")
print("Subscores:", result.subscores.to_dict())
```

---

## Unit Testing

Execute the comprehensive unit test suite:

```bash
python -m unittest -v test_cdai_crohns.py
```

Test suite coverage:
- Exact multipliers ($x_1 \times 2, x_2 \times 5, x_3 \times 7, x_4 \times 20, x_5 \times 30, x_6 \times 10, x_7 \times 6, x_8 \times 1$).
- Hematocrit baseline differences by biological sex ($47\%$ male vs $42\%$ female).
- Weight percentage deviation and overweight clamping.
- All 4 clinical severity tiers (<150, 150-219, 220-450, >450).
- Harvey-Bradshaw Index (HBI) validation.
- Clinical trial endpoints (CR-70, CR-100, Remission).
- Boundary validation and error raising for invalid inputs.

---

## References

1. **Best WR, Becktel JM, Singleton JW, Kern F Jr.** Development of a Crohn's disease activity index. National Cooperative Crohn's Disease Study. *Gastroenterology*. 1976;70(3):439-444.
2. **Best WR.** Predicting the Crohn's disease activity index from the Harvey-Bradshaw Index. *Inflamm Bowel Dis*. 2006;12(4):304-310.
3. **Harvey RF, Bradshaw JM.** A simple index of Crohn's-disease activity. *Lancet*. 1980;1(8167):514.
4. **Sandborn WJ, Feagan BG, Hanauer SB, et al.** A review of activity indices and efficacy endpoints for clinical trials of medical therapy in adults with Crohn's disease. *Gastroenterology*. 2002;122(2):512-530.

---

## License

MIT License.
