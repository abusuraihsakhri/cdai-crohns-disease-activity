#!/usr/bin/env python3
"""
Unit Test Suite for Crohn's Disease Activity Index (CDAI) & HBI Engine
=====================================================================
Comprehensive tests covering the Best et al. (1976) CDAI formulations,
Harvey-Bradshaw Index (HBI), clinical trial response metrics, boundary checks,
and edge cases.
"""

import json
import unittest
from cdai_crohns import (
    CDAIInput,
    CDAIComplications,
    CDAIResult,
    CDAISeverity,
    HBISeverity,
    AbdominalMass,
    BiologicalSex,
    calculate_cdai,
    calculate_hbi,
    compare_cdai_trial_endpoints,
    HBIInput,
    HBIResult,
    _parse_dict_to_cdai_input,
)


class TestCDAIEngine(unittest.TestCase):

    # 1. Component Multiplier & Exact Formulation Tests
    def test_stools_multiplier_exact(self):
        # 10 stools * 2 = 20 pts
        inp = CDAIInput(
            liquid_stools_7day_sum=10, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            hematocrit=47.0, sex=BiologicalSex.MALE, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp)
        self.assertEqual(res.subscores.stools_score, 20.0)
        self.assertAlmostEqual(res.score, 20.0, places=1)

    def test_pain_multiplier_exact(self):
        # 7 pain * 5 = 35 pts
        inp = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=7, wellbeing_7day_sum=0,
            hematocrit=47.0, sex=BiologicalSex.MALE, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp)
        self.assertEqual(res.subscores.pain_score, 35.0)
        self.assertAlmostEqual(res.score, 35.0, places=1)

    def test_wellbeing_multiplier_exact(self):
        # 10 wellbeing * 7 = 70 pts
        inp = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=10,
            hematocrit=47.0, sex=BiologicalSex.MALE, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp)
        self.assertEqual(res.subscores.wellbeing_score, 70.0)
        self.assertAlmostEqual(res.score, 70.0, places=1)

    def test_complications_multiplier_exact(self):
        # 3 complications * 20 = 60 pts
        comp = CDAIComplications(
            arthritis_or_arthralgia=True,
            mucocutaneous_lesions=True,
            iritis_or_uveitis=True,
        )
        inp = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            complications=comp, hematocrit=47.0, sex=BiologicalSex.MALE,
            actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp)
        self.assertEqual(res.subscores.complications_score, 60.0)
        self.assertAlmostEqual(res.score, 60.0, places=1)

    def test_antidiarrheal_multiplier_exact(self):
        # 1 * 30 = 30 pts
        inp = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            taking_antidiarrheals=True, hematocrit=47.0, sex=BiologicalSex.MALE,
            actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp)
        self.assertEqual(res.subscores.antidiarrheal_score, 30.0)
        self.assertAlmostEqual(res.score, 30.0, places=1)

    def test_abdominal_mass_scores(self):
        # None = 0, Questionable = 20, Definite = 50
        base_kwargs = dict(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            hematocrit=47.0, sex=BiologicalSex.MALE, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res_none = calculate_cdai(CDAIInput(abdominal_mass=AbdominalMass.NONE, **base_kwargs))
        res_quest = calculate_cdai(CDAIInput(abdominal_mass=AbdominalMass.QUESTIONABLE, **base_kwargs))
        res_def = calculate_cdai(CDAIInput(abdominal_mass=AbdominalMass.DEFINITE, **base_kwargs))

        self.assertEqual(res_none.subscores.mass_score, 0.0)
        self.assertEqual(res_quest.subscores.mass_score, 20.0)
        self.assertEqual(res_def.subscores.mass_score, 50.0)

    def test_hematocrit_deficit_male_vs_female(self):
        # Male standard is 47%, Female standard is 42%
        # Male with Hct 37 -> (47 - 37) * 6 = 60 pts
        inp_m = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            hematocrit=37.0, sex=BiologicalSex.MALE, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res_m = calculate_cdai(inp_m)
        self.assertEqual(res_m.subscores.hematocrit_score, 60.0)

        # Female with Hct 37 -> (42 - 37) * 6 = 30 pts
        inp_f = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            hematocrit=37.0, sex=BiologicalSex.FEMALE, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res_f = calculate_cdai(inp_f)
        self.assertEqual(res_f.subscores.hematocrit_score, 30.0)

    def test_body_weight_deviation(self):
        # Standard weight 70 kg, actual weight 63 kg -> (1 - 63/70) * 100 = 10% deficit -> 10 pts
        inp = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            hematocrit=47.0, sex=BiologicalSex.MALE, actual_weight_kg=63.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp)
        self.assertAlmostEqual(res.subscores.body_weight_score, 10.0, places=1)

    def test_overweight_clamping(self):
        # Patient is overweight: 100 kg actual vs 70 kg std -> (1 - 100/70)*100 = -42.8%
        # Should be clamped at -10 pts
        inp = CDAIInput(
            liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            hematocrit=47.0, sex=BiologicalSex.MALE, actual_weight_kg=100.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp, clamp_overweight=True)
        self.assertEqual(res.subscores.body_weight_score, -10.0)

    # 2. Comprehensive Severity Classification Tiers
    def test_clinical_remission_tier(self):
        # Score < 150
        inp = CDAIInput(
            liquid_stools_7day_sum=7,   # 14
            abdominal_pain_7day_sum=3,  # 15
            wellbeing_7day_sum=4,       # 28
            taking_antidiarrheals=False,# 0
            abdominal_mass=AbdominalMass.NONE, # 0
            hematocrit=45.0,            # (47-45)*6 = 12
            sex=BiologicalSex.MALE,
            actual_weight_kg=70.0,
            standard_weight_kg=70.0,    # 0
        )
        # Total = 14 + 15 + 28 + 0 + 0 + 0 + 12 + 0 = 69
        res = calculate_cdai(inp)
        self.assertEqual(res.score, 69.0)
        self.assertEqual(res.severity, CDAISeverity.REMISSION)
        self.assertTrue(res.is_remission)

    def test_mildly_active_tier(self):
        # Score 150 - 219
        inp = CDAIInput(
            liquid_stools_7day_sum=15,  # 30
            abdominal_pain_7day_sum=7,  # 35
            wellbeing_7day_sum=8,       # 56
            taking_antidiarrheals=True, # 30
            abdominal_mass=AbdominalMass.NONE, # 0
            hematocrit=44.0,            # (47-44)*6 = 18
            sex=BiologicalSex.MALE,
            actual_weight_kg=68.0,
            standard_weight_kg=70.0,    # (1-68/70)*100 = 2.86
        )
        # Total = 30 + 35 + 56 + 0 + 30 + 0 + 18 + 2.86 = 171.86
        res = calculate_cdai(inp)
        self.assertGreaterEqual(res.score, 150.0)
        self.assertLess(res.score, 220.0)
        self.assertEqual(res.severity, CDAISeverity.MILD)
        self.assertFalse(res.is_remission)

    def test_moderately_active_tier(self):
        # Score 220 - 450
        comp = CDAIComplications(arthritis_or_arthralgia=True, anal_fissure_fistula_abscess=True) # 40
        inp = CDAIInput(
            liquid_stools_7day_sum=25,  # 50
            abdominal_pain_7day_sum=12, # 60
            wellbeing_7day_sum=14,      # 98
            complications=comp,         # 40
            taking_antidiarrheals=True, # 30
            abdominal_mass=AbdominalMass.QUESTIONABLE, # 20
            hematocrit=38.0,            # (47-38)*6 = 54
            sex=BiologicalSex.MALE,
            actual_weight_kg=65.0,
            standard_weight_kg=70.0,    # (1 - 65/70)*100 = 7.14
        )
        # Total = 50 + 60 + 98 + 40 + 30 + 20 + 54 + 7.14 = 359.14
        res = calculate_cdai(inp)
        self.assertGreaterEqual(res.score, 220.0)
        self.assertLessEqual(res.score, 450.0)
        self.assertEqual(res.severity, CDAISeverity.MODERATE)

    def test_severely_active_tier(self):
        # Score > 450
        comp = CDAIComplications(
            arthritis_or_arthralgia=True, mucocutaneous_lesions=True,
            anal_fissure_fistula_abscess=True, fever_over_37_8c_past_week=True
        ) # 80
        inp = CDAIInput(
            liquid_stools_7day_sum=40,  # 80
            abdominal_pain_7day_sum=18, # 90
            wellbeing_7day_sum=22,      # 154
            complications=comp,         # 80
            taking_antidiarrheals=True, # 30
            abdominal_mass=AbdominalMass.DEFINITE, # 50
            hematocrit=32.0,            # (47-32)*6 = 90
            sex=BiologicalSex.MALE,
            actual_weight_kg=55.0,
            standard_weight_kg=70.0,    # (1 - 55/70)*100 = 21.43
        )
        # Total = 80 + 90 + 154 + 80 + 30 + 50 + 90 + 21.43 = 595.43
        res = calculate_cdai(inp)
        self.assertGreater(res.score, 450.0)
        self.assertEqual(res.severity, CDAISeverity.SEVERE)

    # 3. Harvey-Bradshaw Index (HBI) Tests
    def test_hbi_remission(self):
        hbi_in = HBIInput(general_wellbeing=0, abdominal_pain=0, liquid_stools_day=2, abdominal_mass=0)
        res = calculate_hbi(hbi_in)
        self.assertEqual(res.score, 2)
        self.assertEqual(res.severity, HBISeverity.REMISSION)
        self.assertTrue(res.is_remission)

    def test_hbi_mild_activity(self):
        hbi_in = HBIInput(general_wellbeing=1, abdominal_pain=1, liquid_stools_day=4, abdominal_mass=0)
        res = calculate_hbi(hbi_in)
        self.assertEqual(res.score, 6)
        self.assertEqual(res.severity, HBISeverity.MILD)

    def test_hbi_moderate_activity(self):
        hbi_in = HBIInput(
            general_wellbeing=2, abdominal_pain=2, liquid_stools_day=5,
            abdominal_mass=1, arthralgia=True, aphthous_ulcers=True
        )
        # Score = 2 + 2 + 5 + 1 + 2 = 12
        res = calculate_hbi(hbi_in)
        self.assertEqual(res.score, 12)
        self.assertEqual(res.severity, HBISeverity.MODERATE)

    def test_hbi_severe_activity(self):
        hbi_in = HBIInput(
            general_wellbeing=3, abdominal_pain=3, liquid_stools_day=8,
            abdominal_mass=2, arthralgia=True, uveitis=True, pyoderma_gangrenosum=True
        )
        # Score = 3 + 3 + 8 + 2 + 3 = 19
        res = calculate_hbi(hbi_in)
        self.assertEqual(res.score, 19)
        self.assertEqual(res.severity, HBISeverity.SEVERE)

    # 4. Clinical Trial Endpoint Comparisons (CR-70 / CR-100 / Remission)
    def test_cr70_and_cr100_endpoints_achieved(self):
        base_inp = CDAIInput(liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0, hematocrit=42.0)
        base_res = calculate_cdai(base_inp)
        base_res.score = 350.0

        post_res = calculate_cdai(base_inp)
        post_res.score = 140.0  # Drop = 210, Remission (<150)

        comp = compare_cdai_trial_endpoints(base_res, post_res)
        self.assertTrue(comp.cr70_achieved)
        self.assertTrue(comp.cr100_achieved)
        self.assertTrue(comp.remission_achieved)
        self.assertAlmostEqual(comp.absolute_delta, 210.0)

    def test_cr70_met_cr100_unmet(self):
        base_inp = CDAIInput(liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0, hematocrit=42.0)
        base_res = calculate_cdai(base_inp)
        base_res.score = 320.0

        post_res = calculate_cdai(base_inp)
        post_res.score = 240.0  # Drop = 80 (>=70, <100), not remission

        comp = compare_cdai_trial_endpoints(base_res, post_res)
        self.assertTrue(comp.cr70_achieved)
        self.assertFalse(comp.cr100_achieved)
        self.assertFalse(comp.remission_achieved)

    def test_disease_flare_comparison(self):
        base_inp = CDAIInput(liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0, hematocrit=42.0)
        base_res = calculate_cdai(base_inp)
        base_res.score = 120.0

        post_res = calculate_cdai(base_inp)
        post_res.score = 280.0  # Flare up

        comp = compare_cdai_trial_endpoints(base_res, post_res)
        self.assertFalse(comp.cr70_achieved)
        self.assertFalse(comp.remission_achieved)
        self.assertLess(comp.absolute_delta, 0.0)

    # 5. Input Validation & Error Handling
    def test_negative_stools_raises_value_error(self):
        inp = CDAIInput(
            liquid_stools_7day_sum=-5, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
            hematocrit=42.0, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        with self.assertRaises(ValueError):
            calculate_cdai(inp)

    def test_out_of_bounds_pain_raises_value_error(self):
        inp = CDAIInput(
            liquid_stools_7day_sum=10, abdominal_pain_7day_sum=25, wellbeing_7day_sum=0,  # Max is 21
            hematocrit=42.0, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        with self.assertRaises(ValueError):
            calculate_cdai(inp)

    def test_out_of_bounds_wellbeing_raises_value_error(self):
        inp = CDAIInput(
            liquid_stools_7day_sum=10, abdominal_pain_7day_sum=5, wellbeing_7day_sum=35,  # Max is 28
            hematocrit=42.0, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        with self.assertRaises(ValueError):
            calculate_cdai(inp)

    def test_non_physiological_hematocrit_raises_value_error(self):
        inp = CDAIInput(
            liquid_stools_7day_sum=10, abdominal_pain_7day_sum=5, wellbeing_7day_sum=5,
            hematocrit=75.0, actual_weight_kg=70.0, standard_weight_kg=70.0  # 75% invalid
        )
        with self.assertRaises(ValueError):
            calculate_cdai(inp)

    def test_negative_weight_raises_value_error(self):
        inp = CDAIInput(
            liquid_stools_7day_sum=10, abdominal_pain_7day_sum=5, wellbeing_7day_sum=5,
            hematocrit=40.0, actual_weight_kg=-50.0, standard_weight_kg=70.0
        )
        with self.assertRaises(ValueError):
            calculate_cdai(inp)

    # 6. Dictionary & Serialization Utilities
    def test_dict_input_parsing(self):
        raw_dict = {
            "stools": 14,
            "pain": 7,
            "wellbeing": 10,
            "arthralgia": True,
            "hct": 38.0,
            "sex": "FEMALE",
            "weight_kg": 60.0,
            "standard_weight": 65.0,
        }
        res = calculate_cdai(raw_dict)
        self.assertIsInstance(res, CDAIResult)
        self.assertGreater(res.score, 0.0)

    def test_json_serialization(self):
        inp = CDAIInput(
            liquid_stools_7day_sum=14, abdominal_pain_7day_sum=7, wellbeing_7day_sum=10,
            hematocrit=42.0, sex=BiologicalSex.MALE, actual_weight_kg=70.0, standard_weight_kg=70.0
        )
        res = calculate_cdai(inp)
        d = res.to_dict()
        self.assertIn("score", d)
        self.assertIn("subscores", d)
        self.assertIn("clinical_interpretation", d)
        json_str = json.dumps(d)
        self.assertIn("subscores", json_str)


if __name__ == "__main__":
    unittest.main()
