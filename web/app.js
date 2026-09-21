    "use strict";
    const $ = (id) => document.getElementById(id);
    const api = window.CDAICalculator;
    const themeKey = "cdai-theme";

    function setTheme(theme) {
      document.documentElement.dataset.theme = theme;
      $("themeToggle").textContent = theme === "dark" ? "Light" : "Dark";
      $("themeToggle").setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} theme`);
    }
    const savedTheme = localStorage.getItem(themeKey);
    setTheme(savedTheme === "dark" ? "dark" : "light");
    $("themeToggle").addEventListener("click", () => {
      const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      localStorage.setItem(themeKey, next); setTheme(next);
    });

    document.querySelectorAll(".tab").forEach((button) => button.addEventListener("click", () => {
      const name = button.dataset.tab;
      document.querySelectorAll(".tab").forEach((b) => b.setAttribute("aria-selected", String(b === button)));
      document.querySelectorAll("[data-panel]").forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== name));
    }));

    function checked(id) { return $(id).checked; }
    function val(id) { return $(id).value; }
    function clearError(id) { $(id).textContent = ""; }
    function showError(id, error) { $(id).textContent = error instanceof Error ? error.message : String(error); }
    function yesNo(value) { return value ? "Met" : "Not met"; }

    function renderCDAI() {
      clearError("cdaiError");
      try {
        const result = api.calculateCDAI({
          stools: val("cdaiStools"), pain: val("cdaiPain"), wellbeing: val("cdaiWellbeing"), mass: val("cdaiMass"),
          hct: val("cdaiHct"), sex: val("cdaiSex"), actualWeight: val("cdaiWeight"), standardWeight: val("cdaiStdWeight"),
          arthralgia: checked("cArthralgia"), skinLesions: checked("cSkin"), uveitis: checked("cUveitis"), perianal: checked("cPerianal"),
          otherFistula: checked("cFistula"), fever: checked("cFever"), antidiarrheal: checked("cAnti")
        });
        $("cdaiScore").textContent = result.score.toFixed(1);
        $("cdaiSeverity").textContent = result.severity.label;
        $("cdaiRange").textContent = result.severity.range;
        $("cdaiNote").textContent = result.note;
        const labels = { stools: "Stools ×2", pain: "Pain ×5", wellbeing: "Well-being ×7", complications: `Complications ×20 (${result.complicationCount})`, antidiarrheal: "Antidiarrheal ×30", mass: "Mass ×10", hematocrit: "Hematocrit ×6", weight: "Weight deviation" };
        const tbody = $("cdaiBreakdown"); tbody.replaceChildren();
        Object.entries(result.parts).forEach(([key, points]) => {
          const row = document.createElement("tr"); const name = document.createElement("td"); const value = document.createElement("td");
          name.textContent = labels[key]; value.textContent = points.toFixed(1); row.append(name, value); tbody.append(row);
        });
      } catch (error) { showError("cdaiError", error); }
    }
    $("cdaiForm").addEventListener("submit", (e) => { e.preventDefault(); renderCDAI(); });
    $("cdaiReset").addEventListener("click", () => { $("cdaiForm").reset(); clearError("cdaiError"); $("cdaiScore").textContent = "—"; $("cdaiSeverity").textContent = "Enter values and calculate"; $("cdaiRange").textContent = ""; $("cdaiBreakdown").innerHTML = '<tr><td colspan="2">No calculation yet.</td></tr>'; });

    function renderHBI() {
      clearError("hbiError");
      try {
        const result = api.calculateHBI({ wellbeing: val("hbiWellbeing"), pain: val("hbiPain"), stools: val("hbiStools"), mass: val("hbiMass"), arthralgia: checked("hArthralgia"), uveitis: checked("hUveitis"), erythema: checked("hErythema"), aphthous: checked("hAphthous"), pyoderma: checked("hPyoderma"), perianal: checked("hPerianal"), otherFistula: checked("hFistula"), abscess: checked("hAbscess") });
        $("hbiScore").textContent = String(result.score); $("hbiSeverity").textContent = result.severity.label; $("hbiRange").textContent = result.severity.range; $("hbiComplications").textContent = String(result.complicationCount); $("hbiNote").textContent = result.note;
      } catch (error) { showError("hbiError", error); }
    }
    $("hbiForm").addEventListener("submit", (e) => { e.preventDefault(); renderHBI(); });
    $("hbiReset").addEventListener("click", () => { $("hbiForm").reset(); clearError("hbiError"); $("hbiScore").textContent = "—"; $("hbiSeverity").textContent = "Enter values and calculate"; $("hbiRange").textContent = ""; $("hbiComplications").textContent = "—"; });

    function renderTrial() {
      clearError("trialError");
      try {
        const result = api.compareCDAI({ baseline: val("baseline"), post: val("post") });
        $("trialDelta").textContent = result.delta.toFixed(1); $("trialPercent").textContent = `${result.percentageReduction.toFixed(1)}% reduction from baseline`; $("trialCr70").textContent = yesNo(result.cr70); $("trialCr100").textContent = yesNo(result.cr100); $("trialRemission").textContent = yesNo(result.remission);
      } catch (error) { showError("trialError", error); }
    }
    $("trialForm").addEventListener("submit", (e) => { e.preventDefault(); renderTrial(); });
    $("trialReset").addEventListener("click", () => { $("trialForm").reset(); clearError("trialError"); $("trialDelta").textContent = "—"; $("trialPercent").textContent = "Enter values and compare"; ["trialCr70","trialCr100","trialRemission"].forEach((id) => $(id).textContent = "—"); });
