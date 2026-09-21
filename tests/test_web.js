"use strict";
const assert = require("node:assert/strict");
const { calculateCDAI, calculateHBI, compareCDAI, flag } = require("../web/calculator.js");

assert.equal(flag("0"), false);
assert.equal(flag("1"), true);
assert.equal(flag("false"), false);
assert.equal(flag("true"), true);

const remission = calculateCDAI({
  stools: 7, pain: 2, wellbeing: 3, mass: 0, hct: 44, sex: "MALE", actualWeight: 72, standardWeight: 72,
  arthralgia: "0", skinLesions: "0", uveitis: "0", perianal: "0", otherFistula: "0", fever: "0", antidiarrheal: "0"
});
assert.equal(remission.score, 63);
assert.equal(remission.complicationCount, 0);
assert.equal(remission.severity.key, "REMISSION");

const complicated = calculateCDAI({
  stools: 14, pain: 5, wellbeing: 7, mass: 0, hct: 39, sex: "FEMALE", actualWeight: 58, standardWeight: 60,
  arthralgia: "1", skinLesions: "0", uveitis: "0", perianal: "0", otherFistula: "0", fever: "0", antidiarrheal: "0"
});
assert.equal(complicated.complicationCount, 1);

assert.throws(() => calculateCDAI({ stools: 0, pain: 22, wellbeing: 0, mass: 0, hct: 42, sex: "FEMALE", actualWeight: 70, standardWeight: 70 }), /between 0 and 21/);
assert.throws(() => calculateCDAI({ stools: 0, pain: 0, wellbeing: 0, mass: 0, hct: 42, sex: "UNKNOWN", actualWeight: 70, standardWeight: 70 }), /MALE or FEMALE/);

const hbi = calculateHBI({ wellbeing: 2, pain: 2, stools: 5, mass: 1, arthralgia: true, aphthous: true });
assert.equal(hbi.score, 12);
assert.equal(hbi.severity.key, "MODERATELY_ACTIVE");
assert.throws(() => calculateHBI({ wellbeing: 5, pain: 0, stools: 0, mass: 0 }), /between 0 and 4/);

const trial = compareCDAI({ baseline: 320, post: 140 });
assert.equal(trial.delta, 180);
assert.equal(trial.cr70, true);
assert.equal(trial.cr100, true);
assert.equal(trial.remission, true);
assert.throws(() => compareCDAI({ baseline: -1, post: 0 }), /non-negative/);

console.log("Browser calculation tests passed.");
