#!/usr/bin/env python3
"""Command-line interface for the CDAI/HBI calculator."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import List, Optional

from cdai_crohns import (
    AbdominalMass,
    BiologicalSex,
    CDAIComplications,
    CDAIInput,
    calculate_cdai,
    calculate_hbi,
    compare_cdai_trial_endpoints,
    HBIInput,
)


def _print_error(exc: Exception) -> int:
    print(f"Error: {exc}", file=sys.stderr)
    return 2


def run_cdai_single(args: argparse.Namespace) -> int:
    try:
        comp = CDAIComplications(
            arthritis_or_arthralgia=args.arthralgia,
            mucocutaneous_lesions=args.skin_lesions,
            iritis_or_uveitis=args.uveitis,
            anal_fissure_fistula_abscess=args.perianal,
            other_bowel_fistula=args.other_fistula,
            fever_over_37_8c_past_week=args.fever,
        )
        result = calculate_cdai(
            CDAIInput(
                liquid_stools_7day_sum=args.stools,
                abdominal_pain_7day_sum=args.pain,
                wellbeing_7day_sum=args.wellbeing,
                complications=comp,
                taking_antidiarrheals=args.antidiarrheals,
                abdominal_mass=AbdominalMass(args.mass),
                hematocrit=args.hct,
                sex=BiologicalSex.FEMALE if args.sex.upper().startswith("F") else BiologicalSex.MALE,
                actual_weight_kg=args.weight,
                standard_weight_kg=args.std_weight,
            )
        )
    except (TypeError, ValueError) as exc:
        return _print_error(exc)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    print("=" * 62)
    print("CROHN'S DISEASE ACTIVITY INDEX (CDAI)")
    print("=" * 62)
    print(f"Score:       {result.score:.1f}")
    print(f"Category:    {result.severity.value}")
    print(f"Remission:   {'YES' if result.is_remission else 'NO'}")
    print("-" * 62)
    for key, value in result.subscores.to_dict().items():
        print(f"{key:<28} {value:>7.1f}")
    print("-" * 62)
    print(result.clinical_interpretation)
    print(result.action_recommendations[0])
    return 0


def run_hbi(args: argparse.Namespace) -> int:
    try:
        result = calculate_hbi(
            HBIInput(
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
        )
    except (TypeError, ValueError) as exc:
        return _print_error(exc)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    print("=" * 62)
    print("HARVEY-BRADSHAW INDEX (HBI)")
    print("=" * 62)
    print(f"Score:       {result.score}")
    print(f"Category:    {result.severity.value}")
    print(f"Remission:   {'YES' if result.is_remission else 'NO'}")
    print(result.clinical_interpretation)
    print(result.predicted_cdai_range)
    return 0


def run_compare(args: argparse.Namespace) -> int:
    try:
        baseline = calculate_cdai(CDAIInput(0, 0, 0, hematocrit=42.0))
        post = calculate_cdai(CDAIInput(0, 0, 0, hematocrit=42.0))
        baseline.score = args.baseline
        post.score = args.post
        comparison = compare_cdai_trial_endpoints(baseline, post)
    except (TypeError, ValueError) as exc:
        return _print_error(exc)

    if args.json:
        print(json.dumps(comparison.to_dict(), indent=2))
        return 0

    print("=" * 62)
    print("CDAI RESPONSE ENDPOINT COMPARISON")
    print("=" * 62)
    print(f"Baseline:    {comparison.baseline_score:.1f}")
    print(f"Post:        {comparison.post_treatment_score:.1f}")
    print(f"Change:      {comparison.absolute_delta:+.1f}")
    print(f"CR-70:       {'MET' if comparison.cr70_achieved else 'NOT MET'}")
    print(f"CR-100:      {'MET' if comparison.cr100_achieved else 'NOT MET'}")
    print(f"Remission:   {'MET' if comparison.remission_achieved else 'NOT MET'}")
    return 0


def run_batch(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.input):
        print(f"Error: input file '{args.input}' not found.", file=sys.stderr)
        return 1

    try:
        with open(args.input, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("input CSV has no header")
            rows = list(reader)
            fieldnames = list(reader.fieldnames)
    except (OSError, csv.Error, ValueError) as exc:
        return _print_error(exc)

    output_fields = fieldnames + ["cdai_score", "cdai_severity", "is_remission", "interpretation", "error"]
    output_rows = []
    errors = 0

    for row_number, row in enumerate(rows, start=2):
        output = dict(row)
        try:
            result = calculate_cdai(row)
            output.update(
                cdai_score=f"{result.score:.1f}",
                cdai_severity=result.severity.value,
                is_remission="YES" if result.is_remission else "NO",
                interpretation=result.clinical_interpretation,
                error="",
            )
        except (TypeError, ValueError) as exc:
            errors += 1
            output.update(
                cdai_score="",
                cdai_severity="",
                is_remission="",
                interpretation="",
                error=f"row {row_number}: {exc}",
            )
        output_rows.append(output)

    try:
        with open(args.output, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=output_fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(output_rows)
    except OSError as exc:
        return _print_error(exc)

    print(f"Processed {len(output_rows)} records into '{args.output}' ({errors} row errors).")
    return 2 if errors else 0


def run_interactive(_: argparse.Namespace) -> int:
    print("Interactive mode is intentionally conservative. Enter the 7-day CDAI sums.")

    def ask_int(prompt: str, default: int) -> int:
        raw = input(f"{prompt} [{default}]: ").strip()
        return int(raw) if raw else default

    def ask_float(prompt: str, default: float) -> float:
        raw = input(f"{prompt} [{default}]: ").strip()
        return float(raw) if raw else default

    try:
        args = argparse.Namespace(
            stools=ask_int("Liquid/soft stools (7-day sum)", 14),
            pain=ask_int("Abdominal pain (7-day sum, 0-21)", 7),
            wellbeing=ask_int("General well-being (7-day sum, 0-28)", 10),
            arthralgia=False,
            skin_lesions=False,
            uveitis=False,
            perianal=False,
            other_fistula=False,
            fever=False,
            antidiarrheals=False,
            mass=0,
            hct=ask_float("Hematocrit (%)", 40.0),
            sex=(input("Sex for CDAI hematocrit term (M/F) [M]: ").strip() or "M"),
            weight=ask_float("Actual weight (kg)", 65.0),
            std_weight=ask_float("Standard weight (kg)", 70.0),
            json=False,
        )
    except ValueError as exc:
        return _print_error(exc)
    return run_cdai_single(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CDAI and HBI calculator")
    subparsers = parser.add_subparsers(dest="command")

    cdai = subparsers.add_parser("cdai", help="Calculate CDAI")
    cdai.add_argument("--stools", type=int, default=14)
    cdai.add_argument("--pain", type=int, default=7)
    cdai.add_argument("--wellbeing", type=int, default=10)
    cdai.add_argument("--arthralgia", action="store_true")
    cdai.add_argument("--skin-lesions", action="store_true")
    cdai.add_argument("--uveitis", action="store_true")
    cdai.add_argument("--perianal", action="store_true")
    cdai.add_argument("--other-fistula", action="store_true")
    cdai.add_argument("--fever", action="store_true")
    cdai.add_argument("--antidiarrheals", action="store_true")
    cdai.add_argument("--mass", type=int, choices=[0, 2, 5], default=0)
    cdai.add_argument("--hct", type=float, default=42.0)
    cdai.add_argument("--sex", choices=["M", "F", "MALE", "FEMALE", "male", "female"], default="M")
    cdai.add_argument("--weight", type=float, default=70.0)
    cdai.add_argument("--std-weight", type=float, default=70.0)
    cdai.add_argument("--json", action="store_true")

    hbi = subparsers.add_parser("hbi", help="Calculate HBI")
    hbi.add_argument("--wellbeing", type=int, choices=range(0, 5), default=1)
    hbi.add_argument("--pain", type=int, choices=range(0, 4), default=1)
    hbi.add_argument("--stools", type=int, default=3)
    hbi.add_argument("--mass", type=int, choices=range(0, 4), default=0)
    hbi.add_argument("--arthralgia", action="store_true")
    hbi.add_argument("--uveitis", action="store_true")
    hbi.add_argument("--skin-lesions", action="store_true")
    hbi.add_argument("--aphthous", action="store_true")
    hbi.add_argument("--pyoderma", action="store_true")
    hbi.add_argument("--perianal", action="store_true")
    hbi.add_argument("--other-fistula", action="store_true")
    hbi.add_argument("--abscess", action="store_true")
    hbi.add_argument("--json", action="store_true")

    compare = subparsers.add_parser("compare", help="Compare baseline and post-treatment CDAI")
    compare.add_argument("--baseline", type=float, required=True)
    compare.add_argument("--post", type=float, required=True)
    compare.add_argument("--json", action="store_true")

    batch = subparsers.add_parser("batch", help="Process a cohort CSV")
    batch.add_argument("--input", "-i", required=True)
    batch.add_argument("--output", "-o", default="cdai_results.csv")

    subparsers.add_parser("interactive", help="Interactive CDAI entry")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    raw_args = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    if not raw_args:
        if sys.stdin.isatty():
            return run_interactive(argparse.Namespace())
        parser.print_help()
        return 0

    args = parser.parse_args(raw_args)
    handlers = {
        "cdai": run_cdai_single,
        "hbi": run_hbi,
        "compare": run_compare,
        "batch": run_batch,
        "interactive": run_interactive,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
