# Crohn's Disease Activity Index (CDAI) & HBI Calculator

A small, dependency-free implementation of the Crohn's Disease Activity Index (CDAI), Harvey-Bradshaw Index (HBI), and common CDAI trial response checks. The repository includes a Python library/CLI and a static browser calculator suitable for GitHub Pages.

## Features

- CDAI calculation from the eight published component terms.
- HBI calculation with input validation.
- CR-70, CR-100, and post-treatment CDAI <150 endpoint checks.
- CSV batch processing from the command line.
- Browser-only calculator with light/dark themes and no server dependency.
- No external runtime Python packages.

## Browser application

The static application is in `web/`. All calculations run locally in the browser; clinical inputs are not sent to an API or stored by the application. The only browser preference stored locally is the selected color theme.

GitHub Pages deployment is handled by `.github/workflows/pages.yml`. The verified live application link is added here after the first successful deployment.

## CDAI formulation

The implementation follows the eight-term CDAI formulation described by Best et al.:

```text
CDAI = 2 × stools
     + 5 × abdominal pain
     + 7 × general well-being
     + 20 × complications
     + 30 × antidiarrheal use
     + 10 × abdominal mass
     + 6 × hematocrit deviation
     + body-weight deviation
```

The program uses the original sex-specific hematocrit reference values (47% male, 42% female), and caps the negative body-weight contribution at -10 points when the patient is above standard weight. The activity labels used by the implementation are: <150 remission/quiescent, 150–219 mildly active, 220–450 moderately active, and >450 severely active.

CDAI is an activity index, not a stand-alone treatment algorithm. The software reports score interpretation but does not prescribe medication, admission, imaging, or other management based only on the score.

## HBI

The Harvey-Bradshaw Index implementation sums general well-being, abdominal pain, daily liquid stools, abdominal mass, and one point for each listed complication. The interface reports the HBI category directly and does not convert HBI into an estimated CDAI range; the two indices are correlated but are not interchangeable.

## Command-line use

Python 3.10 or later is recommended.

```bash
git clone https://github.com/abusuraihsakhri/cdai-crohns-disease-activity.git
cd cdai-crohns-disease-activity

python cli.py cdai \
  --stools 14 --pain 7 --wellbeing 10 \
  --hct 38.5 --sex MALE --weight 65 --std-weight 70

python cli.py hbi --wellbeing 2 --pain 1 --stools 4 --mass 1 --arthralgia
python cli.py compare --baseline 320 --post 140
python cli.py batch --input sample.csv --output results.csv
```

For machine-readable single-calculation output, add `--json` to `cdai`, `hbi`, or `compare`.

## Python API

```python
from cdai_crohns import BiologicalSex, CDAIInput, calculate_cdai

result = calculate_cdai(
    CDAIInput(
        liquid_stools_7day_sum=14,
        abdominal_pain_7day_sum=7,
        wellbeing_7day_sum=10,
        hematocrit=38.5,
        sex=BiologicalSex.MALE,
        actual_weight_kg=65.0,
        standard_weight_kg=70.0,
    )
)

print(result.score)
print(result.severity.value)
```

## CSV input

`sample.csv` shows the supported column names. Boolean columns accept explicit forms such as `0`/`1`, `false`/`true`, and `no`/`yes`. Invalid or ambiguous boolean strings are rejected rather than silently treated as true.

## Development and testing

```bash
python -m pip install pytest
python -m pytest -q
python -m compileall -q cdai_crohns.py cli.py
node tests/test_web.js
python cli.py batch --input sample.csv --output out_smoke.csv
```

The GitHub Actions workflow runs the Python test suite on Python 3.10, 3.11, and 3.12, exercises the CLI batch path, and tests the browser calculation module with Node.js.

## Browser compatibility

The browser UI uses standard HTML, CSS, and JavaScript without a build step or external client libraries. Current versions of Chrome, Edge, Firefox, and Safari are expected to work. JavaScript must be enabled.

## Privacy and clinical-use note

The browser application has no analytics or network API calls and does not persist entered clinical values. The Python CLI reads only the files explicitly supplied by the user. This repository is a research/educational implementation of published scoring formulas and has not undergone independent clinical software or medical-device validation. Verify results and applicability before clinical or research use.

## References

- Best WR, Becktel JM, Singleton JW, Kern F Jr. Development of a Crohn's disease activity index. *Gastroenterology*. 1976;70(3):439-444. PMID: 1248701.
- Harvey RF, Bradshaw JM. A simple index of Crohn's-disease activity. *Lancet*. 1980;1(8167):514.
- Best WR. Predicting the Crohn's disease activity index from the Harvey-Bradshaw Index. *Inflamm Bowel Dis*. 2006;12(4):304-310. PMID: 16633052.

## License

MIT. See [LICENSE](LICENSE).
