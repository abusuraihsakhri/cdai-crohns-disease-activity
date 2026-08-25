#!/usr/bin/env python3
"""
Crohn's Disease Activity Index (CDAI) CLI
=========================================
Production command line interface for CDAI & HBI calculation,
trial efficacy endpoint comparison (CR-70/CR-100), and batch cohort processing.

Usage:
    python cli.py cdai --stools 14 --pain 7 --wellbeing 10 --hct 38.5 --sex MALE --weight 65 --std-weight 70
    python cli.py hbi --wellbeing 2 --pain 1 --stools 4 --mass 1 --arthralgia
    python cli.py interactive
    python cli.py compare --baseline 320 --post 140
    python cli.py batch --input patients.csv --output results.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional

from cdai_crohns import (
    CDAIInput,
    CDAIComplications,
    CDAIResult,
    AbdominalMass,
    BiologicalSex,
    calculate_cdai,
    calculate_hbi,
    compare_cdai_trial_endpoints,
    HBIInput,
    HBIResult,
)


def run_cdai_single(args: argparse.Namespace) -> int:
    mass_enum = AbdominalMass.NONE
    if args.mass >= 4 or str(args.mass).lower() == "definite":
        mass_enum = AbdominalMass.DEFINITE
    elif args.mass >= 2 or str(args.mass).lower() in ["questionable", "equivocal"]:
        mass_enum = AbdominalMass.QUESTIONABLE

    sex_enum = BiologicalSex.FEMALE if args.sex.upper() in ["F", "FEMALE"] else BiologicalSex.MALE

    comp = CDAIComplications(
        arthritis_or_arthralgia=args.arthralgia,
        mucocutaneous_lesions=args.skin_lesions,
        iritis_or_uveitis=args.uveitis,
        anal_fissure_fistula_abscess=args.perianal,
        other_bowel_fistula=args.other_fistula,
        fever_over_37_8c_past_week=args.fever,
    )

    cdai_in = CDAIInput(
        liquid_stools_7day_sum=args.stools,
        abdominal_pain_7day_sum=args.pain,
        wellbeing_7day_sum=args.wellbeing,
        complications=comp,
        taking_antidiarrheals=args.antidiarrheals,
        abdominal_mass=mass_enum,
        hematocrit=args.hct,
        sex=sex_enum,
        actual_weight_kg=args.weight,
        standard_weight_kg=args.std_weight,
    )

    res = calculate_cdai(cdai_in)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0

    print("=" * 65)
    print("  CROHN'S DISEASE ACTIVITY INDEX (CDAI) ASSESSMENT")
    print("=" * 65)
    print(f"Total CDAI Score:  {res.score:.1f}")
    print(f"Severity Tier:     {res.severity.value}")
    print(f"Clinical Remission: {'YES (CDAI < 150)' if res.is_remission else 'NO'}")
    print("-" * 65)
    print("Subcomponent Point Contributions:")
    for k, v in res.subscores.to_dict().items():
        print(f"  - {k:<25}: {v:>6.1f} pts")
    print("-" * 65)
    print(f"Interpretation: {res.clinical_interpretation}")
    print("\nClinical Recommendations:")
    for idx, r in enumerate(res.action_recommendations, 1):
        print(f"  {idx}. {r}")
    print("=" * 65)
    return 0


def run_hbi(args: argparse.Namespace) -> int:
    hbi_in = HBIInput(
        general_wellbeing=args.wellbeing,
        abdominal_pain=args.pain,
        liquid_stools_day=args.stools,
        abdominal_mass=args.mass,
        arthralgia=args.arthralgia,
        uveitis=args.uveitis,
        erythema_nodosum=args.skin_lesions,
        aphthous_ulcers=args.aphthous,
        pyoderma_gangrenosum=args.pyoderma,
        anal_fissure_or_fistula=args.perianal,
        other_fistula=args.other_fistula,
        abscess=args.abscess,
    )

    res = calculate_hbi(hbi_in)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0

    print("=" * 65)
    print("  HARVEY-BRADSHAW INDEX (HBI) ASSESSMENT")
    print("=" * 65)
    print(f"Total HBI Score:   {res.score}")
    print(f"Severity Tier:     {res.severity.value}")
    print(f"Predicted CDAI:    {res.predicted_cdai_range}")
    print(f"Interpretation:    {res.clinical_interpretation}")
    print("=" * 65)
    return 0


def run_compare(args: argparse.Namespace) -> int:
    base_in = CDAIInput(
        liquid_stools_7day_sum=0, abdominal_pain_7day_sum=0, wellbeing_7day_sum=0,
        hematocrit=42.0, actual_weight_kg=70.0, standard_weight_kg=70.0
    )
    # create dummy result objects to utilize the endpoint comparison
    base_res = calculate_cdai(base_in)
    base_res.score = args.baseline

    post_res = calculate_cdai(base_in)
    post_res.score = args.post

    comp = compare_cdai_trial_endpoints(base_res, post_res)

    if args.json:
        print(json.dumps(comp.to_dict(), indent=2))
        return 0

    print("=" * 65)
    print("  CDAI LONGITUDINAL & CLINICAL TRIAL RESPONSE COMPARISON")
    print("=" * 65)
    print(f"Baseline CDAI:       {comp.baseline_score:.1f}")
    print(f"Post-Treatment CDAI: {comp.post_treatment_score:.1f}")
    print(f"Absolute Delta:      {comp.absolute_delta:.1f} points ({comp.percentage_reduction:.1f}% reduction)")
    print("-" * 65)
    print(f"CR-70 Endpoint (Delta >= 70 pts):   {'ACHIEVED [PASS]' if comp.cr70_achieved else 'FAILED [NOT MET]'}")
    print(f"CR-100 Endpoint (Delta >= 100 pts): {'ACHIEVED [PASS]' if comp.cr100_achieved else 'FAILED [NOT MET]'}")
    print(f"Clinical Remission (Post < 150):    {'ACHIEVED [PASS]' if comp.remission_achieved else 'FAILED [NOT MET]'}")
    print("-" * 65)
    print(f"Summary: {comp.therapeutic_response_summary}")
    print("=" * 65)
    return 0


def run_batch(args: argparse.Namespace) -> int:
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        return 1

    with open(args.input, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    out_fields = fieldnames + ["cdai_score", "cdai_severity", "is_remission", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        try:
            res = calculate_cdai(r)
            row_dict = dict(r)
            row_dict["cdai_score"] = round(res.score, 1)
            row_dict["cdai_severity"] = res.severity.value
            row_dict["is_remission"] = "YES" if res.is_remission else "NO"
            row_dict["clinical_recommendation"] = res.action_recommendations[0] if res.action_recommendations else ""
            out_rows.append(row_dict)
        except Exception as e:
            row_dict = dict(r)
            row_dict["cdai_score"] = "ERROR"
            row_dict["cdai_severity"] = str(e)
            row_dict["is_remission"] = "NO"
            row_dict["clinical_recommendation"] = ""
            out_rows.append(row_dict)

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Successfully processed {len(out_rows)} records into '{args.output}'.")
    return 0


def run_interactive(args: argparse.Namespace) -> int:
    print("=" * 65)
    print("  CROHN'S DISEASE ACTIVITY INDEX (CDAI) INTERACTIVE WIZARD")
    print("=" * 65)

    def ask_int(prompt: str, default: int = 0) -> int:
        val = input(f"{prompt} [{default}]: ").strip()
        return int(val) if val.isdigit() else default

    def ask_float(prompt: str, default: float = 0.0) -> float:
        val = input(f"{prompt} [{default}]: ").strip()
        try:
            return float(val) if val else default
        except ValueError:
            return default

    def ask_bool(prompt: str) -> bool:
        val = input(f"{prompt} (y/N): ").strip().lower()
        return val in ["y", "yes", "true", "1"]

    stools = ask_int("1. Total number of liquid or very soft stools over 7 days", 14)
    pain = ask_int("2. Abdominal pain rating sum over 7 days (0=none to 3=severe per day; max 21)", 7)
    wellbeing = ask_int("3. General well-being rating sum over 7 days (0=well to 4=terrible per day; max 28)", 10)

    print("\n4. Extra-intestinal Manifestations / Complications:")
    arth = ask_bool("   - Arthritis or arthralgia?")
    skin = ask_bool("   - Mucocutaneous lesions (erythema nodosum, aphthous ulcers, pyoderma)?")
    uveitis = ask_bool("   - Iritis or uveitis?")
    perianal = ask_bool("   - Anal fissure, fistula, or abscess?")
    fistula = ask_bool("   - Other bowel fistula?")
    fever = ask_bool("   - Fever > 37.8 C (100 F) during the past week?")

    anti = ask_bool("\n5. Taking loperamide, Lomotil, or opiates for diarrhea?")
    
    print("\n6. Abdominal Mass:")
    print("   0 = None, 2 = Questionable/Equivocal, 5 = Definite mass")
    mass_val = ask_int("   Enter mass score (0, 2, or 5)", 0)
    mass_enum = AbdominalMass.DEFINITE if mass_val >= 4 else (AbdominalMass.QUESTIONABLE if mass_val >= 2 else AbdominalMass.NONE)

    sex_str = input("\n7. Patient biological sex (M/F) [M]: ").strip().upper() or "M"
    sex_enum = BiologicalSex.FEMALE if sex_str in ["F", "FEMALE"] else BiologicalSex.MALE

    hct = ask_float("8. Hematocrit percentage (e.g. 38.5)", 40.0)
    actual_w = ask_float("9. Patient's actual body weight (kg)", 65.0)
    std_w = ask_float("10. Standard / ideal body weight for height (kg)", 70.0)

    comp = CDAIComplications(
        arthritis_or_arthralgia=arth,
        mucocutaneous_lesions=skin,
        iritis_or_uveitis=uveitis,
        anal_fissure_fistula_abscess=perianal,
        other_bowel_fistula=fistula,
        fever_over_37_8c_past_week=fever,
    )

    cdai_in = CDAIInput(
        liquid_stools_7day_sum=stools,
        abdominal_pain_7day_sum=pain,
        wellbeing_7day_sum=wellbeing,
        complications=comp,
        taking_antidiarrheals=anti,
        abdominal_mass=mass_enum,
        hematocrit=hct,
        sex=sex_enum,
        actual_weight_kg=actual_w,
        standard_weight_kg=std_w,
    )

    res = calculate_cdai(cdai_in)

    print("\n" + "=" * 65)
    print(f"Total CDAI Score:   {res.score:.1f}")
    print(f"Severity Tier:      {res.severity.value}")
    print(f"Clinical Remission: {'YES (CDAI < 150)' if res.is_remission else 'NO'}")
    print("-" * 65)
    print("Point Breakdown:")
    for k, v in res.subscores.to_dict().items():
        print(f"  {k:<25}: {v:>6.1f} pts")
    print("-" * 65)
    print(f"Guidance: {res.clinical_interpretation}")
    print("=" * 65)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="CDAI & HBI Calculator - Clinical Activity Index for Crohn's Disease"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # CDAI subcommand
    cdai_p = subparsers.add_parser("cdai", help="Calculate Crohn's Disease Activity Index (7-day)")
    cdai_p.add_argument("--stools", type=int, default=14, help="7-day sum of liquid/soft stools")
    cdai_p.add_argument("--pain", type=int, default=7, help="7-day sum of abdominal pain (0-21)")
    cdai_p.add_argument("--wellbeing", type=int, default=10, help="7-day sum of general wellbeing (0-28)")
    cdai_p.add_argument("--arthralgia", action="store_true", help="Presence of arthritis/arthralgia")
    cdai_p.add_argument("--skin-lesions", action="store_true", help="Presence of erythema nodosum/pyoderma/aphthous ulcers")
    cdai_p.add_argument("--uveitis", action="store_true", help="Presence of iritis/uveitis")
    cdai_p.add_argument("--perianal", action="store_true", help="Presence of anal fissure, fistula, or abscess")
    cdai_p.add_argument("--other-fistula", action="store_true", help="Presence of other bowel fistula")
    cdai_p.add_argument("--fever", action="store_true", help="Fever > 37.8 C during past week")
    cdai_p.add_argument("--antidiarrheals", action="store_true", help="Taking Lomotil/opiates for diarrhea")
    cdai_p.add_argument("--mass", type=int, default=0, help="Abdominal mass (0=none, 2=questionable, 5=definite)")
    cdai_p.add_argument("--hct", type=float, default=42.0, help="Hematocrit percentage (e.g. 38.5)")
    cdai_p.add_argument("--sex", choices=["MALE", "FEMALE", "M", "F", "male", "female"], default="MALE", help="Biological sex")
    cdai_p.add_argument("--weight", type=float, default=70.0, help="Actual weight (kg)")
    cdai_p.add_argument("--std-weight", type=float, default=70.0, help="Standard weight for height (kg)")
    cdai_p.add_argument("--json", action="store_true", help="Output JSON result")

    # HBI subcommand
    hbi_p = subparsers.add_parser("hbi", help="Calculate Harvey-Bradshaw Index (1-day)")
    hbi_p.add_argument("--wellbeing", type=int, default=1, help="Well-being (0=very well to 4=terrible)")
    hbi_p.add_argument("--pain", type=int, default=1, help="Abdominal pain (0=none, 1=mild, 2=mod, 3=severe)")
    hbi_p.add_argument("--stools", type=int, default=3, help="Number of liquid stools per day")
    hbi_p.add_argument("--mass", type=int, default=0, help="Abdominal mass (0=none, 1=dubious, 2=definite, 3=tender)")
    hbi_p.add_argument("--arthralgia", action="store_true", help="Arthritis / arthralgia")
    hbi_p.add_argument("--uveitis", action="store_true", help="Iritis / uveitis")
    hbi_p.add_argument("--skin-lesions", action="store_true", help="Erythema nodosum")
    hbi_p.add_argument("--aphthous", action="store_true", help="Aphthous ulcers")
    hbi_p.add_argument("--pyoderma", action="store_true", help="Pyoderma gangrenosum")
    hbi_p.add_argument("--perianal", action="store_true", help="Anal fissure or fistula")
    hbi_p.add_argument("--other-fistula", action="store_true", help="Other fistula")
    hbi_p.add_argument("--abscess", action="store_true", help="Abscess")
    hbi_p.add_argument("--json", action="store_true", help="Output JSON result")

    # Compare subcommand
    comp_p = subparsers.add_parser("compare", help="Compare baseline vs post-treatment CDAI scores (CR-70 / CR-100)")
    comp_p.add_argument("--baseline", type=float, required=True, help="Baseline CDAI score")
    comp_p.add_argument("--post", type=float, required=True, help="Post-treatment CDAI score")
    comp_p.add_argument("--json", action="store_true", help="Output JSON result")

    # Batch subcommand
    batch_p = subparsers.add_parser("batch", help="Batch process CSV cohort file")
    batch_p.add_argument("--input", "-i", required=True, help="Input CSV file path")
    batch_p.add_argument("--output", "-o", default="cdai_results.csv", help="Output CSV file path")

    # Interactive subcommand
    subparsers.add_parser("interactive", help="Interactive CDAI calculation wizard")

    args = parser.parse_args(argv)

    if args.command == "cdai":
        return run_cdai_single(args)
    elif args.command == "hbi":
        return run_hbi(args)
    elif args.command == "compare":
        return run_compare(args)
    elif args.command == "batch":
        return run_batch(args)
    elif args.command == "interactive":
        return run_interactive(args)
    else:
        if len(sys.argv) == 1:
            return run_interactive(args)
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
