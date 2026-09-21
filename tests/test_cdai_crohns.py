import json
import subprocess
import sys
from pathlib import Path

import pytest

from cdai_crohns import (
    AbdominalMass,
    BiologicalSex,
    CDAIComplications,
    CDAIInput,
    CDAISeverity,
    HBIInput,
    HBISeverity,
    _parse_dict_to_cdai_input,
    calculate_cdai,
    calculate_hbi,
    compare_cdai_trial_endpoints,
)


def neutral_cdai(**overrides):
    values = dict(
        liquid_stools_7day_sum=0,
        abdominal_pain_7day_sum=0,
        wellbeing_7day_sum=0,
        hematocrit=47.0,
        sex=BiologicalSex.MALE,
        actual_weight_kg=70.0,
        standard_weight_kg=70.0,
    )
    values.update(overrides)
    return CDAIInput(**values)


def test_component_weights():
    assert calculate_cdai(neutral_cdai(liquid_stools_7day_sum=10)).subscores.stools_score == 20
    assert calculate_cdai(neutral_cdai(abdominal_pain_7day_sum=7)).subscores.pain_score == 35
    assert calculate_cdai(neutral_cdai(wellbeing_7day_sum=10)).subscores.wellbeing_score == 70
    assert calculate_cdai(neutral_cdai(taking_antidiarrheals=True)).subscores.antidiarrheal_score == 30
    assert calculate_cdai(neutral_cdai(abdominal_mass=AbdominalMass.QUESTIONABLE)).subscores.mass_score == 20
    assert calculate_cdai(neutral_cdai(abdominal_mass=AbdominalMass.DEFINITE)).subscores.mass_score == 50


def test_complications_weight():
    complications = CDAIComplications(
        arthritis_or_arthralgia=True,
        mucocutaneous_lesions=True,
        iritis_or_uveitis=True,
    )
    result = calculate_cdai(neutral_cdai(complications=complications))
    assert result.subscores.complications_score == 60


def test_hematocrit_reference_differs_by_sex():
    male = calculate_cdai(neutral_cdai(hematocrit=37.0))
    female = calculate_cdai(neutral_cdai(hematocrit=37.0, sex=BiologicalSex.FEMALE))
    assert male.subscores.hematocrit_score == 60
    assert female.subscores.hematocrit_score == 30


def test_weight_deviation_and_overweight_clamp():
    deficit = calculate_cdai(neutral_cdai(actual_weight_kg=63.0))
    overweight = calculate_cdai(neutral_cdai(actual_weight_kg=100.0))
    assert deficit.subscores.body_weight_score == pytest.approx(10.0)
    assert overweight.subscores.body_weight_score == -10.0


def test_cdai_categories():
    remission = calculate_cdai(neutral_cdai(liquid_stools_7day_sum=7, abdominal_pain_7day_sum=3, wellbeing_7day_sum=4, hematocrit=45.0))
    mild = calculate_cdai(neutral_cdai(liquid_stools_7day_sum=15, abdominal_pain_7day_sum=7, wellbeing_7day_sum=8, taking_antidiarrheals=True, hematocrit=44.0, actual_weight_kg=68.0))
    moderate = calculate_cdai(neutral_cdai(liquid_stools_7day_sum=25, abdominal_pain_7day_sum=12, wellbeing_7day_sum=14, taking_antidiarrheals=True, abdominal_mass=AbdominalMass.QUESTIONABLE, hematocrit=38.0, actual_weight_kg=65.0, complications=CDAIComplications(arthritis_or_arthralgia=True, anal_fissure_fistula_abscess=True)))
    severe = calculate_cdai(neutral_cdai(liquid_stools_7day_sum=40, abdominal_pain_7day_sum=18, wellbeing_7day_sum=22, taking_antidiarrheals=True, abdominal_mass=AbdominalMass.DEFINITE, hematocrit=32.0, actual_weight_kg=55.0, complications=CDAIComplications(arthritis_or_arthralgia=True, mucocutaneous_lesions=True, iritis_or_uveitis=True, anal_fissure_fistula_abscess=True)))
    assert remission.severity is CDAISeverity.REMISSION
    assert mild.severity is CDAISeverity.MILD
    assert moderate.severity is CDAISeverity.MODERATE
    assert severe.severity is CDAISeverity.SEVERE


def test_csv_zero_strings_are_false_regression():
    parsed = _parse_dict_to_cdai_input({
        "stools": "7", "pain": "2", "wellbeing": "3", "arthralgia": "0",
        "skin_lesions": "0", "uveitis": "0", "fistula": "0", "fever": "0",
        "antidiarrheal": "0", "abdominal_mass": "none", "hct": "44", "sex": "M",
        "weight_kg": "72", "standard_weight": "72",
    })
    assert parsed.complications.count() == 0
    assert parsed.taking_antidiarrheals is False
    result = calculate_cdai(parsed)
    assert result.score == pytest.approx(63.0)


def test_csv_one_strings_are_true():
    parsed = _parse_dict_to_cdai_input({
        "stools": "0", "pain": "0", "wellbeing": "0", "arthralgia": "1",
        "antidiarrheal": "1", "abdominal_mass": "0", "hct": "47", "sex": "M",
        "weight_kg": "70", "standard_weight": "70",
    })
    assert parsed.complications.count() == 1
    assert parsed.taking_antidiarrheals is True
    assert calculate_cdai(parsed).score == 50.0


@pytest.mark.parametrize("field,value", [
    ("abdominal_pain_7day_sum", 22),
    ("wellbeing_7day_sum", 29),
    ("liquid_stools_7day_sum", -1),
    ("hematocrit", 75.0),
    ("actual_weight_kg", 0.0),
])
def test_invalid_cdai_inputs_raise(field, value):
    with pytest.raises(ValueError):
        calculate_cdai(neutral_cdai(**{field: value}))


def test_invalid_dictionary_values_raise():
    with pytest.raises(ValueError):
        calculate_cdai({"stools": 0, "pain": 0, "wellbeing": 0, "sex": "UNKNOWN"})
    with pytest.raises(ValueError):
        calculate_cdai({"stools": 0, "pain": 0, "wellbeing": 0, "arthralgia": "maybe"})


def test_hbi_categories_and_validation():
    assert calculate_hbi(HBIInput(0, 0, 2, 0)).severity is HBISeverity.REMISSION
    assert calculate_hbi(HBIInput(1, 1, 4, 0)).severity is HBISeverity.MILD
    assert calculate_hbi(HBIInput(2, 2, 5, 1, arthralgia=True, aphthous_ulcers=True)).severity is HBISeverity.MODERATE
    assert calculate_hbi(HBIInput(3, 3, 8, 2, arthralgia=True, uveitis=True, pyoderma_gangrenosum=True)).severity is HBISeverity.SEVERE
    with pytest.raises(ValueError):
        calculate_hbi(HBIInput(5, 0, 0, 0))
    with pytest.raises(ValueError):
        calculate_hbi(HBIInput(0, 0, -1, 0))


def test_hbi_does_not_claim_direct_cdai_conversion():
    result = calculate_hbi(HBIInput(0, 0, 2, 0))
    assert "not directly interchangeable" in result.predicted_cdai_range


def test_trial_endpoints():
    baseline = calculate_cdai(neutral_cdai())
    post = calculate_cdai(neutral_cdai())
    baseline.score = 320.0
    post.score = 140.0
    comparison = compare_cdai_trial_endpoints(baseline, post)
    assert comparison.cr70_achieved
    assert comparison.cr100_achieved
    assert comparison.remission_achieved
    assert comparison.absolute_delta == 180.0


def test_trial_endpoint_rejects_negative_score():
    baseline = calculate_cdai(neutral_cdai())
    post = calculate_cdai(neutral_cdai())
    baseline.score = -1
    with pytest.raises(ValueError):
        compare_cdai_trial_endpoints(baseline, post)


def test_json_serialization():
    payload = calculate_cdai(neutral_cdai()).to_dict()
    assert json.loads(json.dumps(payload))["severity"] == "REMISSION"


def test_cli_batch_sample(tmp_path):
    sample = Path(__file__).parents[1] / "sample.csv"
    output = tmp_path / "out.csv"
    completed = subprocess.run(
        [sys.executable, "cli.py", "batch", "--input", str(sample), "--output", str(output)],
        cwd=Path(__file__).parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    rows = list(csv_dict_reader(output))
    assert rows[0]["cdai_score"] == "63.0"
    assert rows[0]["error"] == ""


def csv_dict_reader(path: Path):
    import csv
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)
