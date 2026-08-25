#!/usr/bin/env python3
"""
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
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


# ==============================================================================
# ENUMS & CONSTANTS
# ==============================================================================

class BiologicalSex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class AbdominalMass(int, Enum):
    NONE = 0
    QUESTIONABLE = 2
    DEFINITE = 5


class CDAISeverity(str, Enum):
    REMISSION = "REMISSION"                     # < 150
    MILD = "MILDLY_ACTIVE"                      # 150 - 219
    MODERATE = "MODERATELY_ACTIVE"              # 220 - 450
    SEVERE = "SEVERELY_ACTIVE"                  # > 450


class HBISeverity(str, Enum):
    REMISSION = "REMISSION"                     # < 5
    MILD = "MILDLY_ACTIVE"                      # 5 - 7
    MODERATE = "MODERATELY_ACTIVE"              # 8 - 16
    SEVERE = "SEVERELY_ACTIVE"                  # > 16


# Standard reference hematocrits (Best et al. 1976)
STANDARD_HEMATOCRIT_MALE = 47.0
STANDARD_HEMATOCRIT_FEMALE = 42.0

# Multipliers from Best et al. (1976)
WEIGHT_STOOLS = 2.0
WEIGHT_PAIN = 5.0
WEIGHT_WELLBEING = 7.0
WEIGHT_COMPLICATIONS = 20.0
WEIGHT_ANTIDIARRHEAL = 30.0
WEIGHT_MASS = 10.0
WEIGHT_HEMATOCRIT = 6.0
WEIGHT_BODY_WEIGHT = 1.0


# ==============================================================================
# DATA STRUCTURES & MODELS
# ==============================================================================

@dataclass
class CDAIComplications:
    """Extra-intestinal manifestations and complications (1 point each if present)."""
    arthritis_or_arthralgia: bool = False
    mucocutaneous_lesions: bool = False   # Erythema nodosum, pyoderma gangrenosum, aphthous stomatitis
    iritis_or_uveitis: bool = False
    anal_fissure_fistula_abscess: bool = False
    other_bowel_fistula: bool = False
    fever_over_37_8c_past_week: bool = False

    def count(self) -> int:
        return sum([
            bool(self.arthritis_or_arthralgia),
            bool(self.mucocutaneous_lesions),
            bool(self.iritis_or_uveitis),
            bool(self.anal_fissure_fistula_abscess),
            bool(self.other_bowel_fistula),
            bool(self.fever_over_37_8c_past_week),
        ])

    def to_dict(self) -> Dict[str, bool]:
        return asdict(self)


@dataclass
class CDAIInput:
    """
    Input parameters for CDAI computation over 7-day diary + clinical exam.
    """
    liquid_stools_7day_sum: int
    abdominal_pain_7day_sum: int          # Sum of daily ratings (0=none, 1=mild, 2=mod, 3=severe; 0-21)
    wellbeing_7day_sum: int               # Sum of daily ratings (0=well, 1=under par, 2=poor, 3=very poor, 4=terrible; 0-28)
    complications: CDAIComplications = field(default_factory=CDAIComplications)
    taking_antidiarrheals: bool = False   # Diphenoxylate, loperamide, opiates for diarrhea
    abdominal_mass: AbdominalMass = AbdominalMass.NONE
    hematocrit: float = 42.0              # In percent (e.g. 38.5)
    sex: BiologicalSex = BiologicalSex.MALE
    actual_weight_kg: float = 70.0
    standard_weight_kg: float = 70.0      # Based on height, sex, and standard tables

    def validate(self) -> List[str]:
        errors = []
        if self.liquid_stools_7day_sum < 0:
            errors.append("liquid_stools_7day_sum must be non-negative.")
        if not (0 <= self.abdominal_pain_7day_sum <= 21):
            errors.append("abdominal_pain_7day_sum must be between 0 and 21 (7 days x max 3).")
        if not (0 <= self.wellbeing_7day_sum <= 28):
            errors.append("wellbeing_7day_sum must be between 0 and 28 (7 days x max 4).")
        if not (10.0 <= self.hematocrit <= 65.0):
            errors.append(f"hematocrit ({self.hematocrit}%) is out of realistic physiological range (10-65%).")
        if self.actual_weight_kg <= 0 or self.standard_weight_kg <= 0:
            errors.append("actual_weight_kg and standard_weight_kg must be positive.")
        return errors


@dataclass
class CDAISubscores:
    """Granular breakdown of CDAI subcomponent points."""
    stools_score: float
    pain_score: float
    wellbeing_score: float
    complications_score: float
    antidiarrheal_score: float
    mass_score: float
    hematocrit_score: float
    body_weight_score: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "stools_score": round(self.stools_score, 2),
            "pain_score": round(self.pain_score, 2),
            "wellbeing_score": round(self.wellbeing_score, 2),
            "complications_score": round(self.complications_score, 2),
            "antidiarrheal_score": round(self.antidiarrheal_score, 2),
            "mass_score": round(self.mass_score, 2),
            "hematocrit_score": round(self.hematocrit_score, 2),
            "body_weight_score": round(self.body_weight_score, 2),
        }


@dataclass
class CDAIResult:
    """Comprehensive calculation result for CDAI."""
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
            "action_recommendations": self.action_recommendations,
            "inputs": self.inputs,
        }


@dataclass
class HBIInput:
    """Harvey-Bradshaw Index (single day clinical evaluation)."""
    general_wellbeing: int       # 0=Very well, 1=Slightly below par, 2=Poor, 3=Very poor, 4=Terrible
    abdominal_pain: int          # 0=None, 1=Mild, 2=Moderate, 3=Severe
    liquid_stools_day: int       # Number of liquid stools per day
    abdominal_mass: int          # 0=None, 1=Dubious, 2=Definite, 3=Definite and tender
    arthralgia: bool = False
    uveitis: bool = False
    erythema_nodosum: bool = False
    aphthous_ulcers: bool = False
    pyoderma_gangrenosum: bool = False
    anal_fissure_or_fistula: bool = False
    other_fistula: bool = False
    abscess: bool = False


@dataclass
class HBIResult:
    """Calculation result for Harvey-Bradshaw Index."""
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
    """Comparative response analysis between baseline and post-treatment CDAI."""
    baseline_score: float
    post_treatment_score: float
    absolute_delta: float         # baseline - post (positive = improvement)
    percentage_reduction: float   # (baseline - post)/baseline * 100
    cr70_achieved: bool           # Drop >= 70 points
    cr100_achieved: bool          # Drop >= 100 points
    remission_achieved: bool      # Post score < 150
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


# ==============================================================================
# CORE COMPUTATIONAL LOGIC
# ==============================================================================

def calculate_cdai(
    input_data: Union[CDAIInput, Dict[str, Any]],
    clamp_overweight: bool = True
) -> CDAIResult:
    """
    Computes the Crohn's Disease Activity Index (CDAI) from clinical inputs.

    Parameters:
        input_data: CDAIInput dataclass or dict of parameters.
        clamp_overweight: If True, caps overweight body weight deviation at 0 or -10
                          according to standard clinical implementations.

    Returns:
        CDAIResult with score, subscores, severity classification, and clinical guidance.
    """
    if isinstance(input_data, dict):
        inp = _parse_dict_to_cdai_input(input_data)
    else:
        inp = input_data

    # Validation
    errors = inp.validate()
    if errors:
        raise ValueError("Invalid CDAI inputs: " + "; ".join(errors))

    # 1. Stools subscore: sum * 2
    stools_sub = inp.liquid_stools_7day_sum * WEIGHT_STOOLS

    # 2. Abdominal pain subscore: sum * 5
    pain_sub = inp.abdominal_pain_7day_sum * WEIGHT_PAIN

    # 3. Well-being subscore: sum * 7
    wellbeing_sub = inp.wellbeing_7day_sum * WEIGHT_WELLBEING

    # 4. Complications subscore: count * 20
    comp_count = inp.complications.count()
    comp_sub = comp_count * WEIGHT_COMPLICATIONS

    # 5. Antidiarrheal drug use: 0 or 1 * 30
    antidiarrheal_sub = (1.0 if inp.taking_antidiarrheals else 0.0) * WEIGHT_ANTIDIARRHEAL

    # 6. Abdominal mass: (0, 2, or 5) * 10
    mass_val = int(inp.abdominal_mass.value if hasattr(inp.abdominal_mass, 'value') else inp.abdominal_mass)
    mass_sub = mass_val * WEIGHT_MASS

    # 7. Hematocrit deficit subscore: (Standard - Actual) * 6
    hct_std = STANDARD_HEMATOCRIT_MALE if inp.sex == BiologicalSex.MALE else STANDARD_HEMATOCRIT_FEMALE
    hct_diff = hct_std - inp.hematocrit
    hct_sub = hct_diff * WEIGHT_HEMATOCRIT

    # 8. Body weight deviation: (1 - actual / standard) * 100 * 1
    pct_deviation = (1.0 - (inp.actual_weight_kg / inp.standard_weight_kg)) * 100.0
    if clamp_overweight and pct_deviation < -10.0:
        # In original Best 1976 regression, overweight patients contribution capped at -10
        pct_deviation = -10.0
    weight_sub = pct_deviation * WEIGHT_BODY_WEIGHT

    total_score = (
        stools_sub
        + pain_sub
        + wellbeing_sub
        + comp_sub
        + antidiarrheal_sub
        + mass_sub
        + hct_sub
        + weight_sub
    )

    subscores = CDAISubscores(
        stools_score=stools_sub,
        pain_score=pain_sub,
        wellbeing_score=wellbeing_sub,
        complications_score=comp_sub,
        antidiarrheal_score=antidiarrheal_sub,
        mass_score=mass_sub,
        hematocrit_score=hct_sub,
        body_weight_score=weight_sub,
    )

    # Severity Tiering
    if total_score < 150.0:
        severity = CDAISeverity.REMISSION
        is_remission = True
        interp = "Clinical Remission (CDAI < 150). Disease is quiescent."
        recs = [
            "Maintain current maintenance therapy (biologic, immunomodulator, or surveillance).",
            "Monitor fecal calprotectin / CRP every 3-6 months to assess subclinical inflammation.",
            "Routine health maintenance and nutritional surveillance.",
        ]
    elif total_score < 220.0:
        severity = CDAISeverity.MILD
        is_remission = False
        interp = "Mildly Active Crohn's Disease (CDAI 150 - 219). Low-grade symptoms."
        recs = [
            "Evaluate for non-inflammatory causes (e.g. bile acid diarrhea, IBS overlap, strictures).",
            "Assess inflammatory markers (fecal calprotectin, CRP) and therapeutic drug monitoring (TDM).",
            "Consider oral budesonide (for ileocecal disease) or optimizing current maintenance dosing.",
        ]
    elif total_score <= 450.0:
        severity = CDAISeverity.MODERATE
        is_remission = False
        interp = "Moderately Active Crohn's Disease (CDAI 220 - 450). Significant systemic & GI burden."
        recs = [
            "Initiate or escalate advanced therapy (Anti-TNF, Anti-IL12/23, Anti-integrin, or JAK inhibitor).",
            "Check serum biologic trough concentrations and anti-drug antibodies.",
            "Consider short-course systemic corticosteroids (prednisone) as bridging therapy.",
            "Cross-sectional imaging (MRE/CT enterography) or colonoscopy to evaluate disease extent/strictures.",
        ]
    else:
        severity = CDAISeverity.SEVERE
        is_remission = False
        interp = "Severely Active / Fulminant Crohn's Disease (CDAI > 450). High risk of hospitalization & surgical complications."
        recs = [
            "URGENT: Consider hospital admission for intravenous corticosteroids, bowel rest, and fluid resuscitation.",
            "Emergency surgical consultation to rule out bowel perforation, toxic megacolon, or intra-abdominal abscess.",
            "Urgent cross-sectional imaging (CT abdomen/pelvis with IV and oral contrast).",
            "Screen for Clostridioides difficile and CMV superinfection prior to intensifying immunosuppression.",
        ]

    input_summary = {
        "liquid_stools_7day_sum": inp.liquid_stools_7day_sum,
        "abdominal_pain_7day_sum": inp.abdominal_pain_7day_sum,
        "wellbeing_7day_sum": inp.wellbeing_7day_sum,
        "complications_count": comp_count,
        "taking_antidiarrheals": inp.taking_antidiarrheals,
        "abdominal_mass": mass_val,
        "hematocrit": inp.hematocrit,
        "sex": inp.sex.value if hasattr(inp.sex, 'value') else inp.sex,
        "actual_weight_kg": inp.actual_weight_kg,
        "standard_weight_kg": inp.standard_weight_kg,
    }

    return CDAIResult(
        score=total_score,
        severity=severity,
        is_remission=is_remission,
        subscores=subscores,
        clinical_interpretation=interp,
        action_recommendations=recs,
        inputs=input_summary,
    )


def calculate_hbi(hbi_in: Union[HBIInput, Dict[str, Any]]) -> HBIResult:
    """
    Computes the Harvey-Bradshaw Index (HBI) for simplified daily assessment.
    """
    if isinstance(hbi_in, dict):
        wellbeing = int(hbi_in.get("general_wellbeing", 0))
        pain = int(hbi_in.get("abdominal_pain", 0))
        stools = int(hbi_in.get("liquid_stools_day", 0))
        mass = int(hbi_in.get("abdominal_mass", 0))
        comp_count = sum([
            bool(hbi_in.get("arthralgia")),
            bool(hbi_in.get("uveitis")),
            bool(hbi_in.get("erythema_nodosum")),
            bool(hbi_in.get("aphthous_ulcers")),
            bool(hbi_in.get("pyoderma_gangrenosum")),
            bool(hbi_in.get("anal_fissure_or_fistula")),
            bool(hbi_in.get("other_fistula")),
            bool(hbi_in.get("abscess")),
        ])
    else:
        wellbeing = hbi_in.general_wellbeing
        pain = hbi_in.abdominal_pain
        stools = hbi_in.liquid_stools_day
        mass = hbi_in.abdominal_mass
        comp_count = sum([
            bool(hbi_in.arthralgia),
            bool(hbi_in.uveitis),
            bool(hbi_in.erythema_nodosum),
            bool(hbi_in.aphthous_ulcers),
            bool(hbi_in.pyoderma_gangrenosum),
            bool(hbi_in.anal_fissure_or_fistula),
            bool(hbi_in.other_fistula),
            bool(hbi_in.abscess),
        ])

    total_hbi = wellbeing + pain + stools + mass + comp_count

    if total_hbi < 5:
        sev = HBISeverity.REMISSION
        is_rem = True
        pred_range = "CDAI < 150 (Quiescent)"
        interp = "Clinical remission based on simplified Harvey-Bradshaw Index."
    elif total_hbi <= 7:
        sev = HBISeverity.MILD
        is_rem = False
        pred_range = "CDAI ~150 - 220 (Mild)"
        interp = "Mildly active Crohn's disease."
    elif total_hbi <= 16:
        sev = HBISeverity.MODERATE
        is_rem = False
        pred_range = "CDAI ~220 - 450 (Moderate)"
        interp = "Moderately active Crohn's disease."
    else:
        sev = HBISeverity.SEVERE
        is_rem = False
        pred_range = "CDAI > 450 (Severe)"
        interp = "Severely active Crohn's disease."

    return HBIResult(
        score=total_hbi,
        severity=sev,
        is_remission=is_rem,
        predicted_cdai_range=pred_range,
        clinical_interpretation=interp,
    )


def compare_cdai_trial_endpoints(baseline: CDAIResult, post: CDAIResult) -> CDAITrialComparison:
    """
    Evaluates standardized clinical trial efficacy endpoints:
    - CR-70: Drop >= 70 points from baseline
    - CR-100: Drop >= 100 points from baseline
    - Clinical Remission: Post-treatment CDAI < 150
    """
    delta = baseline.score - post.score
    pct_red = (delta / baseline.score * 100.0) if baseline.score > 0 else 0.0
    cr70 = delta >= 70.0
    cr100 = delta >= 100.0
    remission = post.score < 150.0

    if remission and cr100:
        summary = f"Optimal Clinical Response & Remission: CDAI dropped by {delta:.1f} pts ({pct_red:.1f}%), reaching Remission (<150)."
    elif remission:
        summary = f"Clinical Remission Achieved: Post-treatment CDAI is {post.score:.1f} (<150)."
    elif cr100:
        summary = f"Substantial Clinical Response (CR-100): CDAI dropped by {delta:.1f} pts, though patient remains in mild/moderate tier."
    elif cr70:
        summary = f"Moderate Clinical Response (CR-70): CDAI dropped by {delta:.1f} pts."
    elif delta > 0:
        summary = f"Minimal Clinical Improvement: CDAI dropped by {delta:.1f} pts (failed CR-70 endpoint)."
    else:
        summary = f"Disease Progression / Lack of Response: CDAI increased by {abs(delta):.1f} pts."

    return CDAITrialComparison(
        baseline_score=baseline.score,
        post_treatment_score=post.score,
        absolute_delta=delta,
        percentage_reduction=pct_red,
        cr70_achieved=cr70,
        cr100_achieved=cr100,
        remission_achieved=remission,
        therapeutic_response_summary=summary,
    )


# ==============================================================================
# HELPER PARSER FOR DICTIONARIES & CSVs
# ==============================================================================

def _parse_dict_to_cdai_input(d: Dict[str, Any]) -> CDAIInput:
    """Converts loose dict or string parameters into structured CDAIInput."""
    sex_str = str(d.get("sex", "MALE")).upper()
    sex = BiologicalSex.FEMALE if sex_str in ["F", "FEMALE"] else BiologicalSex.MALE

    mass_raw = d.get("abdominal_mass", 0)
    if isinstance(mass_raw, str):
        mass_lower = mass_raw.lower()
        if "def" in mass_lower:
            mass = AbdominalMass.DEFINITE
        elif "quest" in mass_lower or "equiv" in mass_lower or "poss" in mass_lower:
            mass = AbdominalMass.QUESTIONABLE
        else:
            try:
                m_int = int(float(mass_raw))
                mass = AbdominalMass.DEFINITE if m_int >= 4 else (AbdominalMass.QUESTIONABLE if m_int >= 2 else AbdominalMass.NONE)
            except ValueError:
                mass = AbdominalMass.NONE
    elif isinstance(mass_raw, (int, float)):
        if mass_raw >= 4:
            mass = AbdominalMass.DEFINITE
        elif mass_raw >= 2:
            mass = AbdominalMass.QUESTIONABLE
        else:
            mass = AbdominalMass.NONE
    else:
        mass = AbdominalMass.NONE

    comp_dict = d.get("complications")
    if isinstance(comp_dict, dict):
        complications = CDAIComplications(
            arthritis_or_arthralgia=bool(comp_dict.get("arthritis_or_arthralgia", False)),
            mucocutaneous_lesions=bool(comp_dict.get("mucocutaneous_lesions", False)),
            iritis_or_uveitis=bool(comp_dict.get("iritis_or_uveitis", False)),
            anal_fissure_fistula_abscess=bool(comp_dict.get("anal_fissure_fistula_abscess", False)),
            other_bowel_fistula=bool(comp_dict.get("other_bowel_fistula", False)),
            fever_over_37_8c_past_week=bool(comp_dict.get("fever_over_37_8c_past_week", False)),
        )
    elif isinstance(comp_dict, (int, float)):
        c_count = int(comp_dict)
        complications = CDAIComplications(
            arthritis_or_arthralgia=c_count > 0,
            mucocutaneous_lesions=c_count > 1,
            iritis_or_uveitis=c_count > 2,
            anal_fissure_fistula_abscess=c_count > 3,
            other_bowel_fistula=c_count > 4,
            fever_over_37_8c_past_week=c_count > 5,
        )
    else:
        complications = CDAIComplications(
            arthritis_or_arthralgia=bool(d.get("arthritis_or_arthralgia", False) or d.get("arthralgia", False)),
            mucocutaneous_lesions=bool(d.get("mucocutaneous_lesions", False) or d.get("skin_lesions", False)),
            iritis_or_uveitis=bool(d.get("iritis_or_uveitis", False) or d.get("uveitis", False)),
            anal_fissure_fistula_abscess=bool(d.get("anal_fissure_fistula_abscess", False) or d.get("fistula", False)),
            other_bowel_fistula=bool(d.get("other_bowel_fistula", False)),
            fever_over_37_8c_past_week=bool(d.get("fever_over_37_8c_past_week", False) or d.get("fever", False)),
        )

    return CDAIInput(
        liquid_stools_7day_sum=int(float(d.get("liquid_stools_7day_sum", d.get("stools", 0)))),
        abdominal_pain_7day_sum=int(float(d.get("abdominal_pain_7day_sum", d.get("pain", 0)))),
        wellbeing_7day_sum=int(float(d.get("wellbeing_7day_sum", d.get("wellbeing", 0)))),
        complications=complications,
        taking_antidiarrheals=bool(d.get("taking_antidiarrheals", d.get("antidiarrheal", False))),
        abdominal_mass=mass,
        hematocrit=float(d.get("hematocrit", d.get("hct", 42.0))),
        sex=sex,
        actual_weight_kg=float(d.get("actual_weight_kg", d.get("weight_kg", 70.0))),
        standard_weight_kg=float(d.get("standard_weight_kg", d.get("standard_weight", 70.0))),
    )
