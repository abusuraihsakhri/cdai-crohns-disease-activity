(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.CDAICalculator = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const HCT_MALE = 47;
  const HCT_FEMALE = 42;

  function finiteNumber(value, label) {
    const n = typeof value === "number" ? value : Number(value);
    if (!Number.isFinite(n)) throw new Error(`${label} must be a finite number.`);
    return n;
  }

  function integer(value, label) {
    const n = finiteNumber(value, label);
    if (!Number.isInteger(n)) throw new Error(`${label} must be an integer.`);
    return n;
  }

  function flag(value) {
    if (typeof value === "boolean") return value;
    if (typeof value === "number") {
      if (value === 1) return true;
      if (value === 0) return false;
    }
    if (typeof value === "string") {
      const normalized = value.trim().toLowerCase();
      if (["1", "true", "yes", "y", "on"].includes(normalized)) return true;
      if (["0", "false", "no", "n", "off", ""].includes(normalized)) return false;
    }
    throw new Error(`Invalid boolean value: ${String(value)}`);
  }

  function severityForCDAI(score) {
    if (score < 150) return { key: "REMISSION", label: "Clinical remission", range: "CDAI < 150" };
    if (score < 220) return { key: "MILDLY_ACTIVE", label: "Mildly active", range: "CDAI 150–219" };
    if (score <= 450) return { key: "MODERATELY_ACTIVE", label: "Moderately active", range: "CDAI 220–450" };
    return { key: "SEVERELY_ACTIVE", label: "Severely active", range: "CDAI > 450" };
  }

  function calculateCDAI(raw) {
    const stools = integer(raw.stools, "7-day liquid/soft stool sum");
    const pain = integer(raw.pain, "7-day abdominal pain sum");
    const wellbeing = integer(raw.wellbeing, "7-day well-being sum");
    const hct = finiteNumber(raw.hct, "Hematocrit");
    const actualWeight = finiteNumber(raw.actualWeight, "Actual weight");
    const standardWeight = finiteNumber(raw.standardWeight, "Standard weight");
    const sex = String(raw.sex || "").trim().toUpperCase();
    const mass = integer(raw.mass, "Abdominal mass score");

    if (stools < 0) throw new Error("7-day liquid/soft stool sum must be non-negative.");
    if (pain < 0 || pain > 21) throw new Error("7-day abdominal pain sum must be between 0 and 21.");
    if (wellbeing < 0 || wellbeing > 28) throw new Error("7-day well-being sum must be between 0 and 28.");
    if (hct < 10 || hct > 65) throw new Error("Hematocrit must be between 10% and 65%.");
    if (actualWeight <= 0 || standardWeight <= 0) throw new Error("Body weights must be greater than 0 kg.");
    if (!["MALE", "FEMALE"].includes(sex)) throw new Error("Sex must be MALE or FEMALE for the original CDAI hematocrit term.");
    if (![0, 2, 5].includes(mass)) throw new Error("Abdominal mass score must be 0, 2, or 5.");

    const complicationKeys = ["arthralgia", "skinLesions", "uveitis", "perianal", "otherFistula", "fever"];
    const complicationCount = complicationKeys.reduce((sum, key) => sum + (flag(raw[key] ?? false) ? 1 : 0), 0);
    const antidiarrheal = flag(raw.antidiarrheal ?? false);

    const parts = {
      stools: stools * 2,
      pain: pain * 5,
      wellbeing: wellbeing * 7,
      complications: complicationCount * 20,
      antidiarrheal: antidiarrheal ? 30 : 0,
      mass: mass * 10,
      hematocrit: ((sex === "MALE" ? HCT_MALE : HCT_FEMALE) - hct) * 6,
      weight: (1 - actualWeight / standardWeight) * 100,
    };
    if (parts.weight < -10) parts.weight = -10;

    const score = Object.values(parts).reduce((sum, n) => sum + n, 0);
    const severity = severityForCDAI(score);

    return {
      score,
      severity,
      remission: score < 150,
      complicationCount,
      parts,
      note: "CDAI is a symptom-based activity index. Interpret it with clinical context and objective assessment; the score alone does not determine treatment.",
    };
  }

  function severityForHBI(score) {
    if (score < 5) return { key: "REMISSION", label: "Clinical remission", range: "HBI < 5" };
    if (score <= 7) return { key: "MILDLY_ACTIVE", label: "Mildly active", range: "HBI 5–7" };
    if (score <= 16) return { key: "MODERATELY_ACTIVE", label: "Moderately active", range: "HBI 8–16" };
    return { key: "SEVERELY_ACTIVE", label: "Severely active", range: "HBI > 16" };
  }

  function calculateHBI(raw) {
    const wellbeing = integer(raw.wellbeing, "General well-being");
    const pain = integer(raw.pain, "Abdominal pain");
    const stools = integer(raw.stools, "Liquid stools per day");
    const mass = integer(raw.mass, "Abdominal mass score");

    if (wellbeing < 0 || wellbeing > 4) throw new Error("General well-being must be between 0 and 4.");
    if (pain < 0 || pain > 3) throw new Error("Abdominal pain must be between 0 and 3.");
    if (stools < 0) throw new Error("Liquid stools per day must be non-negative.");
    if (mass < 0 || mass > 3) throw new Error("Abdominal mass score must be between 0 and 3.");

    const complicationKeys = ["arthralgia", "uveitis", "erythema", "aphthous", "pyoderma", "perianal", "otherFistula", "abscess"];
    const complicationCount = complicationKeys.reduce((sum, key) => sum + (flag(raw[key] ?? false) ? 1 : 0), 0);
    const score = wellbeing + pain + stools + mass + complicationCount;

    return {
      score,
      severity: severityForHBI(score),
      remission: score < 5,
      complicationCount,
      note: "HBI and CDAI are correlated but are not directly interchangeable. Use the index required by your protocol or analysis plan.",
    };
  }

  function compareCDAI(raw) {
    const baseline = finiteNumber(raw.baseline, "Baseline CDAI");
    const post = finiteNumber(raw.post, "Post-treatment CDAI");
    if (baseline < 0 || post < 0) throw new Error("CDAI scores must be non-negative.");
    const delta = baseline - post;
    return {
      baseline,
      post,
      delta,
      percentageReduction: baseline > 0 ? (delta / baseline) * 100 : 0,
      cr70: delta >= 70,
      cr100: delta >= 100,
      remission: post < 150,
    };
  }

  return { calculateCDAI, calculateHBI, compareCDAI, flag };
});
