#!/usr/bin/env python3
"""Crohn's Disease Activity Index (CDAI) and Harvey-Bradshaw Index utilities.

The module implements the published CDAI component weights and a standard HBI
calculation for research, education, and reproducible data processing. It does
not make treatment decisions and is not a validated medical device.

References
----------
Best WR, Becktel JM, Singleton JW, Kern F Jr. Gastroenterology. 1976;70:439-444.
Best WR. Inflamm Bowel Dis. 2006;12:304-310. doi:10.1097/01.MIB.0000215091.77492.2a
Harvey RF, Bradshaw JM. Lancet. 1980;1:514.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Union


class BiologicalSex(str, Enum):
    """Sex category used by the original CDAI hematocrit term."""

    MALE = "MALE"
    FEMALE = "FEMALE"


class AbdominalMass(int, Enum):
    """CDAI abdominal-mass raw values before the x10 multiplier."""

    NONE = 0
    QUESTIONABLE = 2
    DEFINITE = 5


class CDAISeverity(str, Enum):
    REMISSION = "REMISSION"
    MILD = "MILDLY_ACTIVE"
    MODERATE = "MODERATELY_ACTIVE"
    SEVERE = "SEVERELY_ACTIVE"


class HBISeverity(str, Enum):
    REMISSION = "REMISSION"
    MILD = "MILDLY_ACTIVE"
    MODERATE = "MODERATELY_ACTIVE"
    SEVERE = "SEVERELY_ACTIVE"


STANDARD_HEMATOCRIT_MALE = 47.0
STANDARD_HEMATOCRIT_FEMALE = 42.0

WEIGHT_STOOLS = 2.0
WEIGHT_PAIN = 5.0
WEIGHT_WELLBEING = 7.0
WEIGHT_COMPLICATIONS = 20.0
WEIGHT_ANTIDIARRHEAL = 30.0
WEIGHT_MASS = 10.0
WEIGHT_HEMATOCRIT = 6.0
WEIGHT_BODY_WEIGHT = 1.0

_TRUE_STRINGS = {"1", "true", "t", "yes", "y", "on"}
_FALSE_STRINGS = {"0", "false", "f", "no", "n", "off", "", "none", "null", "na", "n/a"}


def _parse_bool(value: Any, *, field_name: str = "value") -> bool:
    """Parse common CSV/CLI boolean representations without truthy-string bugs."""

    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ValueError(f"{field_name} must be a finite boolean-like value")
        if float(value) == 0.0:
            return False
        if float(value) == 1.0:
            return True
        raise ValueError(f"{field_name} must be 0/1 or a boolean value")
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _TRUE_STRINGS:
            return True
        if normalized in _FALSE_STRINGS:
            return False
    raise ValueError(f"{field_name} must be a recognized boolean value")


def _finite_number(value: Any, *, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _integer_number(value: Any, *, field_name: str) -> int:
    number = _finite_number(value, field_name=field_name)
    if not number.is_integer():
        raise ValueError(f"{field_name} must be an integer")
    return int(number)


@dataclass
class CDAIComplications:
    """Extra-intestinal manifestations/complications counted by the CDAI."""

    arthritis_or_arthralgia: bool = False
    mucocutaneous_lesions: bool = False
    iritis_or_uveitis: bool = False
    anal_fissure_fistula_abscess: bool = False
    other_bowel_fistula: bool = False
    fever_over_37_8c_past_week: bool = False

    def count(self) -> int:
        return sum(
            bool(value)
            for value in (
                self.arthritis_or_arthralgia,
                self.mucocutaneous_lesions,
                self.iritis_or_uveitis,
                self.anal_fissure_fistula_abscess,
                self.other_bowel_fistula,
                self.fever_over_37_8c_past_week,
            )
        )

    def to_dict(self) -> Dict[str, bool]:
        return asdict(self)


@dataclass
class CDAIInput:
    """Inputs for CDAI computation using 7-day symptom sums."""

    liquid_stools_7day_sum: int
    abdominal_pain_7day_sum: int
    wellbeing_7day_sum: int
    complications: CDAIComplications = field(default_factory=CDAIComplications)
    taking_antidiarrheals: bool = False
    abdominal_mass: AbdominalMass = AbdominalMass.NONE
    hematocrit: float = 42.0
    sex: BiologicalSex = BiologicalSex.MALE
    actual_weight_kg: float = 70.0
    standard_weight_kg: float = 70.0

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not isinstance(self.liquid_stools_7day_sum, int) or isinstance(self.liquid_stools_7day_sum, bool):
            errors.append("liquid_stools_7day_sum must be an integer.")
        elif self.liquid_stools_7day_sum < 0:
            errors.append("liquid_stools_7day_sum must be non-negative.")

        if not isinstance(self.abdominal_pain_7day_sum, int) or isinstance(self.abdominal_pain_7day_sum, bool):
            errors.append("abdominal_pain_7day_sum must be an integer.")
        elif not 0 <= self.abdominal_pain_7day_sum <= 21:
            errors.append("abdominal_pain_7day_sum must be between 0 and 21.")

        if not isinstance(self.wellbeing_7day_sum, int) or isinstance(self.wellbeing_7day_sum, bool):
            errors.append("wellbeing_7day_sum must be an integer.")
        elif not 0 <= self.wellbeing_7day_sum <= 28:
            errors.append("wellbeing_7day_sum must be between 0 and 28.")

        try:
            hct = float(self.hematocrit)
            if not math.isfinite(hct) or not 10.0 <= hct <= 65.0:
                errors.append("hematocrit must be a finite percentage between 10 and 65.")
        except (TypeError, ValueError):
            errors.append("hematocrit must be numeric.")

        for name, value in (
            ("actual_weight_kg", self.actual_weight_kg),
            ("standard_weight_kg", self.standard_weight_kg),
        ):
            try:
                numeric = float(value)
                if not math.isfinite(numeric) or numeric <= 0:
                    errors.append(f"{name} must be a positive finite number.")
            except (TypeError, ValueError):
                errors.append(f"{name} must be numeric.")

        if not isinstance(self.sex, BiologicalSex):
            errors.append("sex must be BiologicalSex.MALE or BiologicalSex.FEMALE.")
        if not isinstance(self.abdominal_mass, AbdominalMass):
            errors.append("abdominal_mass must be NONE, QUESTIONABLE, or DEFINITE.")
        if not isinstance(self.complications, CDAIComplications):
            errors.append("complications must be a CDAIComplications instance.")
        if not isinstance(self.taking_antidiarrheals, bool):
            errors.append("taking_antidiarrheals must be boolean.")
        return errors


@dataclass
class CDAISubscores:
    stools_score: float
    pain_score: float
    wellbeing_score: float
    complications_score: float
    antidiarrheal_score: float
    mass_score: float
    hematocrit_score: float
    body_weight_score: float

    def to_dict(self) -> Dict[str, float]:
        return {key: round(value, 2) for key, value in asdict(self).items()}


@dataclass
class CDAIResult:
    score: float
    severity: CDAISeverity
    is_remission: bool
    subscores: CDAISubscores
    clinical_interpretation: str
    action_recommendations: List[str]
    inputs: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "severity": self.severity.value,
            "is_remission": self.is_remission,
            "subscores": self.subscores.to_dict(),
            "clinical_interpretation": self.clinical_interpretation,
            "action_recommendations": list(self.action_recommendations),
            "inputs": dict(self.inputs),
        }


@dataclass
class HBIInput:
    general_wellbeing: int
    abdominal_pain: int
    liquid_stools_day: int
    abdominal_mass: int
    arthralgia: bool = False
    uveitis: bool = False
    erythema_nodosum: bool = False
    aphthous_ulcers: bool = False
    pyoderma_gangrenosum: bool = False
    anal_fissure_or_fistula: bool = False
    other_fistula: bool = False
    abscess: bool = False

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not isinstance(self.general_wellbeing, int) or not 0 <= self.general_wellbeing <= 4:
            errors.append("general_wellbeing must be an integer from 0 to 4.")
        if not isinstance(self.abdominal_pain, int) or not 0 <= self.abdominal_pain <= 3:
            errors.append("abdominal_pain must be an integer from 0 to 3.")
        if not isinstance(self.liquid_stools_day, int) or self.liquid_stools_day < 0:
            errors.append("liquid_stools_day must be a non-negative integer.")
        if not isinstance(self.abdominal_mass, int) or not 0 <= self.abdominal_mass <= 3:
            errors.append("abdominal_mass must be an integer from 0 to 3.")
        return errors


@dataclass
class HBIResult:
    score: int
    severity: HBISeverity
    is_remission: bool
    predicted_cdai_range: str
    clinical_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "severity": self.severity.value,
            "is_remission": self.is_remission,
            "predicted_cdai_range": self.predicted_cdai_range,
            "clinical_interpretation": self.clinical_interpretation,
        }


@dataclass
class CDAITrialComparison:
    baseline_score: float
    post_treatment_score: float
    absolute_delta: float
    percentage_reduction: float
    cr70_achieved: bool
    cr100_achieved: bool
    remission_achieved: bool
    therapeutic_response_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_score": round(self.baseline_score, 1),
            "post_treatment_score": round(self.post_treatment_score, 1),
            "absolute_delta": round(self.absolute_delta, 1),
            "percentage_reduction": round(self.percentage_reduction, 1),
            "cr70_achieved": self.cr70_achieved,
            "cr100_achieved": self.cr100_achieved,
            "remission_achieved": self.remission_achieved,
            "therapeutic_response_summary": self.therapeutic_response_summary,
        }


def _severity_from_cdai(score: float) -> CDAISeverity:
    if score < 150.0:
        return CDAISeverity.REMISSION
    if score < 220.0:
        return CDAISeverity.MILD
    if score <= 450.0:
        return CDAISeverity.MODERATE
    return CDAISeverity.SEVERE


def calculate_cdai(
    input_data: Union[CDAIInput, Dict[str, Any]],
    clamp_overweight: bool = True,
) -> CDAIResult:
    """Calculate CDAI and return a component-level result."""

    inp = _parse_dict_to_cdai_input(input_data) if isinstance(input_data, dict) else input_data
    if not isinstance(inp, CDAIInput):
        raise TypeError("input_data must be a CDAIInput or dictionary")

    errors = inp.validate()
    if errors:
        raise ValueError("Invalid CDAI inputs: " + "; ".join(errors))

    comp_count = inp.complications.count()
    mass_val = int(inp.abdominal_mass.value)
    hct_standard = STANDARD_HEMATOCRIT_MALE if inp.sex is BiologicalSex.MALE else STANDARD_HEMATOCRIT_FEMALE
    weight_deviation = (1.0 - (float(inp.actual_weight_kg) / float(inp.standard_weight_kg))) * 100.0
    if clamp_overweight:
        weight_deviation = max(weight_deviation, -10.0)

    subscores = CDAISubscores(
        stools_score=inp.liquid_stools_7day_sum * WEIGHT_STOOLS,
        pain_score=inp.abdominal_pain_7day_sum * WEIGHT_PAIN,
        wellbeing_score=inp.wellbeing_7day_sum * WEIGHT_WELLBEING,
        complications_score=comp_count * WEIGHT_COMPLICATIONS,
        antidiarrheal_score=(1.0 if inp.taking_antidiarrheals else 0.0) * WEIGHT_ANTIDIARRHEAL,
        mass_score=mass_val * WEIGHT_MASS,
        hematocrit_score=(hct_standard - float(inp.hematocrit)) * WEIGHT_HEMATOCRIT,
        body_weight_score=weight_deviation * WEIGHT_BODY_WEIGHT,
    )
    score = sum(asdict(subscores).values())
    severity = _severity_from_cdai(score)

    labels = {
        CDAISeverity.REMISSION: "CDAI below 150 (quiescent/remission range).",
        CDAISeverity.MILD: "CDAI 150-219 (mild activity range).",
        CDAISeverity.MODERATE: "CDAI 220-450 (moderate activity range).",
        CDAISeverity.SEVERE: "CDAI above 450 (very severe activity range).",
    }
    notes = [
        "Use the score as an activity measure, not as a stand-alone treatment recommendation.",
        "Interpret results with the clinical context and objective disease assessment when applicable.",
    ]

    return CDAIResult(
        score=score,
        severity=severity,
        is_remission=score < 150.0,
        subscores=subscores,
        clinical_interpretation=labels[severity],
        action_recommendations=notes,
        inputs={
            "liquid_stools_7day_sum": inp.liquid_stools_7day_sum,
            "abdominal_pain_7day_sum": inp.abdominal_pain_7day_sum,
            "wellbeing_7day_sum": inp.wellbeing_7day_sum,
            "complications_count": comp_count,
            "taking_antidiarrheals": inp.taking_antidiarrheals,
            "abdominal_mass": mass_val,
            "hematocrit": float(inp.hematocrit),
            "sex": inp.sex.value,
            "actual_weight_kg": float(inp.actual_weight_kg),
            "standard_weight_kg": float(inp.standard_weight_kg),
        },
    )


def calculate_hbi(hbi_in: Union[HBIInput, Dict[str, Any]]) -> HBIResult:
    """Calculate the Harvey-Bradshaw Index with explicit range validation."""

    if isinstance(hbi_in, dict):
        inp = HBIInput(
            general_wellbeing=_integer_number(hbi_in.get("general_wellbeing", 0), field_name="general_wellbeing"),
            abdominal_pain=_integer_number(hbi_in.get("abdominal_pain", 0), field_name="abdominal_pain"),
            liquid_stools_day=_integer_number(hbi_in.get("liquid_stools_day", 0), field_name="liquid_stools_day"),
            abdominal_mass=_integer_number(hbi_in.get("abdominal_mass", 0), field_name="abdominal_mass"),
            arthralgia=_parse_bool(hbi_in.get("arthralgia", False), field_name="arthralgia"),
            uveitis=_parse_bool(hbi_in.get("uveitis", False), field_name="uveitis"),
            erythema_nodosum=_parse_bool(hbi_in.get("erythema_nodosum", False), field_name="erythema_nodosum"),
            aphthous_ulcers=_parse_bool(hbi_in.get("aphthous_ulcers", False), field_name="aphthous_ulcers"),
            pyoderma_gangrenosum=_parse_bool(hbi_in.get("pyoderma_gangrenosum", False), field_name="pyoderma_gangrenosum"),
            anal_fissure_or_fistula=_parse_bool(hbi_in.get("anal_fissure_or_fistula", False), field_name="anal_fissure_or_fistula"),
            other_fistula=_parse_bool(hbi_in.get("other_fistula", False), field_name="other_fistula"),
            abscess=_parse_bool(hbi_in.get("abscess", False), field_name="abscess"),
        )
    elif isinstance(hbi_in, HBIInput):
        inp = hbi_in
    else:
        raise TypeError("hbi_in must be an HBIInput or dictionary")

    errors = inp.validate()
    if errors:
        raise ValueError("Invalid HBI inputs: " + "; ".join(errors))

    complications = sum(
        bool(value)
        for value in (
            inp.arthralgia,
            inp.uveitis,
            inp.erythema_nodosum,
            inp.aphthous_ulcers,
            inp.pyoderma_gangrenosum,
            inp.anal_fissure_or_fistula,
            inp.other_fistula,
            inp.abscess,
        )
    )
    score = inp.general_wellbeing + inp.abdominal_pain + inp.liquid_stools_day + inp.abdominal_mass + complications

    if score < 5:
        severity = HBISeverity.REMISSION
        interpretation = "HBI below 5 (remission range)."
    elif score <= 7:
        severity = HBISeverity.MILD
        interpretation = "HBI 5-7 (mild activity range)."
    elif score <= 16:
        severity = HBISeverity.MODERATE
        interpretation = "HBI 8-16 (moderate activity range)."
    else:
        severity = HBISeverity.SEVERE
        interpretation = "HBI above 16 (severe activity range)."

    return HBIResult(
        score=score,
        severity=severity,
        is_remission=score < 5,
        predicted_cdai_range="HBI and CDAI are correlated but are not directly interchangeable.",
        clinical_interpretation=interpretation,
    )


def compare_cdai_trial_endpoints(baseline: CDAIResult, post: CDAIResult) -> CDAITrialComparison:
    """Compare two CDAI results using CR-70, CR-100, and <150 remission endpoints."""

    for name, result in (("baseline", baseline), ("post", post)):
        if not isinstance(result, CDAIResult):
            raise TypeError(f"{name} must be a CDAIResult")
        if not math.isfinite(result.score) or result.score < 0:
            raise ValueError(f"{name} CDAI score must be a non-negative finite number")

    delta = baseline.score - post.score
    percentage = (delta / baseline.score * 100.0) if baseline.score > 0 else 0.0
    cr70 = delta >= 70.0
    cr100 = delta >= 100.0
    remission = post.score < 150.0
    summary = (
        f"Change: {delta:+.1f} CDAI points; "
        f"CR-70 {'met' if cr70 else 'not met'}; "
        f"CR-100 {'met' if cr100 else 'not met'}; "
        f"post-treatment remission threshold {'met' if remission else 'not met'}."
    )

    return CDAITrialComparison(
        baseline_score=baseline.score,
        post_treatment_score=post.score,
        absolute_delta=delta,
        percentage_reduction=percentage,
        cr70_achieved=cr70,
        cr100_achieved=cr100,
        remission_achieved=remission,
        therapeutic_response_summary=summary,
    )


def _parse_dict_to_cdai_input(d: Dict[str, Any]) -> CDAIInput:
    """Convert loose dictionary/CSV values into a validated ``CDAIInput``."""

    if not isinstance(d, dict):
        raise TypeError("d must be a dictionary")

    sex_raw = str(d.get("sex", "MALE")).strip().upper()
    if sex_raw in {"M", "MALE"}:
        sex = BiologicalSex.MALE
    elif sex_raw in {"F", "FEMALE"}:
        sex = BiologicalSex.FEMALE
    else:
        raise ValueError("sex must be M/MALE or F/FEMALE")

    mass_raw = d.get("abdominal_mass", 0)
    if isinstance(mass_raw, str):
        normalized = mass_raw.strip().lower()
        if normalized in {"", "0", "none", "no"}:
            mass = AbdominalMass.NONE
        elif normalized in {"2", "questionable", "equivocal", "possible"}:
            mass = AbdominalMass.QUESTIONABLE
        elif normalized in {"5", "definite", "yes"}:
            mass = AbdominalMass.DEFINITE
        else:
            raise ValueError("abdominal_mass must be 0/none, 2/questionable, or 5/definite")
    else:
        numeric_mass = _integer_number(mass_raw, field_name="abdominal_mass")
        try:
            mass = AbdominalMass(numeric_mass)
        except ValueError as exc:
            raise ValueError("abdominal_mass must be 0, 2, or 5") from exc

    complications_raw = d.get("complications")
    if isinstance(complications_raw, dict):
        complications = CDAIComplications(
            arthritis_or_arthralgia=_parse_bool(complications_raw.get("arthritis_or_arthralgia", False), field_name="arthritis_or_arthralgia"),
            mucocutaneous_lesions=_parse_bool(complications_raw.get("mucocutaneous_lesions", False), field_name="mucocutaneous_lesions"),
            iritis_or_uveitis=_parse_bool(complications_raw.get("iritis_or_uveitis", False), field_name="iritis_or_uveitis"),
            anal_fissure_fistula_abscess=_parse_bool(complications_raw.get("anal_fissure_fistula_abscess", False), field_name="anal_fissure_fistula_abscess"),
            other_bowel_fistula=_parse_bool(complications_raw.get("other_bowel_fistula", False), field_name="other_bowel_fistula"),
            fever_over_37_8c_past_week=_parse_bool(complications_raw.get("fever_over_37_8c_past_week", False), field_name="fever_over_37_8c_past_week"),
        )
    elif complications_raw is not None and str(complications_raw).strip() != "":
        count = _integer_number(complications_raw, field_name="complications")
        if not 0 <= count <= 6:
            raise ValueError("complications count must be between 0 and 6")
        flags = [True] * count + [False] * (6 - count)
        complications = CDAIComplications(*flags)
    else:
        complications = CDAIComplications(
            arthritis_or_arthralgia=_parse_bool(d.get("arthritis_or_arthralgia", d.get("arthralgia", False)), field_name="arthralgia"),
            mucocutaneous_lesions=_parse_bool(d.get("mucocutaneous_lesions", d.get("skin_lesions", False)), field_name="skin_lesions"),
            iritis_or_uveitis=_parse_bool(d.get("iritis_or_uveitis", d.get("uveitis", False)), field_name="uveitis"),
            anal_fissure_fistula_abscess=_parse_bool(d.get("anal_fissure_fistula_abscess", d.get("fistula", False)), field_name="fistula"),
            other_bowel_fistula=_parse_bool(d.get("other_bowel_fistula", False), field_name="other_bowel_fistula"),
            fever_over_37_8c_past_week=_parse_bool(d.get("fever_over_37_8c_past_week", d.get("fever", False)), field_name="fever"),
        )

    return CDAIInput(
        liquid_stools_7day_sum=_integer_number(d.get("liquid_stools_7day_sum", d.get("stools", 0)), field_name="stools"),
        abdominal_pain_7day_sum=_integer_number(d.get("abdominal_pain_7day_sum", d.get("pain", 0)), field_name="pain"),
        wellbeing_7day_sum=_integer_number(d.get("wellbeing_7day_sum", d.get("wellbeing", 0)), field_name="wellbeing"),
        complications=complications,
        taking_antidiarrheals=_parse_bool(d.get("taking_antidiarrheals", d.get("antidiarrheal", False)), field_name="antidiarrheal"),
        abdominal_mass=mass,
        hematocrit=_finite_number(d.get("hematocrit", d.get("hct", 42.0)), field_name="hematocrit"),
        sex=sex,
        actual_weight_kg=_finite_number(d.get("actual_weight_kg", d.get("weight_kg", 70.0)), field_name="actual_weight_kg"),
        standard_weight_kg=_finite_number(d.get("standard_weight_kg", d.get("standard_weight", 70.0)), field_name="standard_weight_kg"),
    )
