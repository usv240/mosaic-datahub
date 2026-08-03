(function () {
  "use strict";

  try {
    const savedTheme = localStorage.getItem("mosaic-theme");
    if (savedTheme) document.documentElement.dataset.theme = savedTheme;
  } catch (error) {
    // Operating-system preference remains the fallback.
  }

  var scenarios = {
    research: {
      title: "Research export investigation",
      subtitle: "Follow the exact evidence chain from DataHub context to a governed proposal.",
      verdict: "Critical",
      verdictClass: "critical",
      k: 1,
      below: 100,
      downstream: 3,
      proposal: "validated_critical",
      finding: "Risk is created by convergence, not by one tagged column.",
      copy: "The per-table baseline reports no compositional finding. DataHub lineage reveals the exact cross-source combination that baseline cannot see.",
      query: "SELECT zip5, birth_date, gender_category,\n       COUNT(*) AS equivalence_class_size\nFROM research_export_clean\nGROUP BY zip5, birth_date, gender_category",
      nodes: [
        { id: "support", label: "Support contacts", detail: "ZIP5 + full birth date", x: 6, y: 13, kind: "source", text: "ZIP5 and full birth date enter through independent column-lineage paths." },
        { id: "demo", label: "Member demographics", detail: "Gender category", x: 6, y: 48, kind: "source", text: "A separate demographic system contributes the third quasi-identifier family." },
        { id: "export", label: "Research export", detail: "3 families converge / k=1", x: 43, y: 31, kind: "risk", text: "DataHub is the only place the cross-source convergence is visible. Aggregate validation finds minimum k=1." },
        { id: "partner", label: "Partner delivery", detail: "Downstream exposure", x: 77, y: 9, kind: "consumer", text: "A research partner delivery inherits the risky column combination." },
        { id: "explorer", label: "Cohort explorer", detail: "Downstream exposure", x: 77, y: 36, kind: "consumer", text: "An interactive cohort export inherits the same privacy exposure." },
        { id: "model", label: "Model training", detail: "Downstream exposure", x: 77, y: 63, kind: "consumer", text: "The training dataset expands the finding's blast radius beyond the original export." }
      ],
      edges: [["support", "export"], ["demo", "export"], ["export", "partner"], ["export", "explorer"], ["export", "model"]]
    },
    mitigated: {
      title: "Privacy-preserving release",
      subtitle: "Compare the original export with a reversible suppression strategy.",
      verdict: "Mitigated",
      verdictClass: "safe",
      k: 20,
      below: 0,
      downstream: 3,
      proposal: "validated_low_after_mitigation",
      finding: "One precise field creates most of the measurable exposure.",
      copy: "Shadow simulation suppresses birth date while retaining ZIP5 and gender category. Minimum anonymity rises to k=20 with 76% analytical utility retained.",
      query: "SELECT zip5, gender_category,\n       COUNT(*) AS equivalence_class_size\nFROM research_export_clean_shadow\nGROUP BY zip5, gender_category",
      nodes: [
        { id: "original", label: "Original export", detail: "ZIP5 + birth date + gender", x: 6, y: 22, kind: "source", text: "The original combination produces 120 singleton equivalence classes." },
        { id: "shadow", label: "Shadow transform", detail: "Suppress birth date", x: 42, y: 22, kind: "source", text: "A reversible simulation removes the precise date without changing the source asset." },
        { id: "release", label: "Safer release", detail: "ZIP5 + gender / k=20", x: 76, y: 22, kind: "consumer", text: "The candidate release meets the visible synthetic-demo policy with minimum k=20." }
      ],
      edges: [["original", "shadow"], ["shadow", "release"]]
    },
    control: {
      title: "Safe negative-control investigation",
      subtitle: "Test whether Mosaic mistakes ordinary high cardinality for compositional privacy risk.",
      verdict: "Clear",
      verdictClass: "clear",
      k: "N/A",
      below: 0,
      downstream: 0,
      proposal: "not_a_compositional_finding",
      finding: "High cardinality alone is not a privacy threat model.",
      copy: "The operational identifier has many distinct values, but it does not join person-level semantic families across lineage paths. Mosaic refuses a critical finding.",
      query: "-- No validation query issued\n-- Candidate rejected before data access:\n-- no multi-family lineage convergence",
      nodes: [
        { id: "ops", label: "Job execution log", detail: "Operational run ID", x: 9, y: 28, kind: "source", text: "The identifier is high-cardinality, but belongs to an operational process rather than a person." },
        { id: "screen", label: "Semantic screen", detail: "No person-joinable family", x: 43, y: 28, kind: "source", text: "Family semantics reject the candidate before any aggregate validation is attempted." },
        { id: "clear", label: "No finding", detail: "False positive avoided", x: 76, y: 28, kind: "consumer", text: "Mosaic records the negative control as clear and performs no write-back mutation." }
      ],
      edges: [["ops", "screen"], ["screen", "clear"]]
    },
    audience: {
      title: "Partner audience investigation",
      subtitle: "See the same privacy mechanism emerge in a second business domain.",
      verdict: "Critical",
      verdictClass: "critical",
      k: 1,
      below: 44.444,
      downstream: 2,
      proposal: "validated_critical",
      finding: "Marketing segments can become quasi-identifiers when the graph combines them.",
      copy: "DataHub shows geography, age band, household segment, and device cohort converging from three systems before two partner-facing deliveries.",
      query: "SELECT geography, age_band, household_segment, device_cohort,\n       COUNT(*) AS equivalence_class_size\nFROM partner_audience_export\nGROUP BY geography, age_band, household_segment, device_cohort",
      nodes: [
        { id: "crm", label: "CRM geography", detail: "Region + household", x: 5, y: 12, kind: "source", text: "CRM contributes geography and household context through fine-grained lineage." },
        { id: "analytics", label: "Product analytics", detail: "Age + device cohort", x: 5, y: 50, kind: "source", text: "Behavioral analytics contributes age band and device cohort from a separate platform." },
        { id: "audience", label: "Audience export", detail: "4 families / k=1", x: 42, y: 31, kind: "risk", text: "The partner audience contains small equivalence classes that neither source reveals alone." },
        { id: "activation", label: "Ad activation", detail: "Downstream exposure", x: 77, y: 16, kind: "consumer", text: "The activation feed inherits the composed audience attributes." },
        { id: "measurement", label: "Campaign measurement", detail: "Downstream exposure", x: 77, y: 51, kind: "consumer", text: "The measurement export extends the blast radius." }
      ],
      edges: [["crm", "audience"], ["analytics", "audience"], ["audience", "activation"], ["audience", "measurement"]]
    }
  };

  var narration = [
    { kicker: "Step 1 - Discover", title: "First, read the map - not the data.", body: "Mosaic asks DataHub where the relevant columns originated and which assets consume them.", why: "Without lineage, each source looks harmless in isolation." },
    { kicker: "Step 2 - Converge", title: "Now connect attributes that meet downstream.", body: "ZIP5, birth date, and gender come from separate systems but converge in the research export.", why: "This cross-system combination is the finding a table-by-table scan misses." },
    { kicker: "Step 3 - Validate", title: "Measure group sizes without viewing a person.", body: "One allowlisted GROUP BY COUNT(*) query returns equivalence-class counts. The smallest count is minimum k.", why: "k=1 means a unique combination. The UI and agent still receive zero raw rows." },
    { kicker: "Step 4 - Defend", title: "Now let hostile metadata try to break the boundary.", body: "A DataHub description asks the agent to ignore policy and export member identifiers with full birth dates.", why: "The request reaches one deterministic choke point, is refused, and returns zero rows." },
    { kicker: "Step 5 - Mitigate", title: "Test safer versions before changing anything.", body: "A shadow simulation compares suppression and generalization strategies against both privacy and retained utility.", why: "The recommended option lifts k to 20 while retaining the most useful detail." },
    { kicker: "Step 6 - Generate", title: "Turn the evidence into a change a team can review.", body: "Mosaic generates a dbt model, aggregate-only test, policy, manifest, and PR summary behind a human gate.", why: "The payoff is code and durable DataHub context—not another dashboard alert." }
  ];
  var selected = "research";
  var running = false;
  var runMessages = [];
  var runStep = -1;
  var runScenario = null;
  var runCompletion = null;
  var startedAt = 0;
  var attackRequestId = 0;
  var attackController = null;
  var codegenRequestId = 0;
  var tourOrder = ["research", "mitigated", "control", "audience"];
  var tourRunning = false;
  var tourIndex = 0;

  function byId(id) { return document.getElementById(id); }
  function all(selector) { return Array.prototype.slice.call(document.querySelectorAll(selector)); }
  function escapeHTML(value) {
    return String(value).replace(/[&<>"]/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[character];
    });
  }

  function currentTheme() {
    var explicit = document.documentElement.dataset.theme;
    if (explicit) return explicit;
    return matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }

  function initTheme() {
    var button = byId("theme-toggle");
    function sync() { button.title = currentTheme() === "light" ? "Switch to dark theme" : "Switch to light theme"; }
    button.addEventListener("click", function () {
      var theme = currentTheme() === "light" ? "dark" : "light";
      document.documentElement.dataset.theme = theme;
      try { localStorage.setItem("mosaic-theme", theme); } catch (error) { /* non-persistent private mode */ }
      sync();
    });
    sync();
  }

  function initHelpTips() {
    var wraps = all(".help-wrap");
    function closeHelpTips() {
      wraps.forEach(function (wrap) {
        var button = wrap.querySelector(".help");
        wrap.classList.remove("is-open");
        button.setAttribute("aria-expanded", "false");
        if (document.activeElement === button) wrap.classList.add("is-dismissed");
      });
    }
    wraps.forEach(function (wrap) {
      var button = wrap.querySelector(".help");
      button.addEventListener("click", function (event) {
        event.stopPropagation();
        var shouldOpen = !wrap.classList.contains("is-open");
        closeHelpTips();
        if (shouldOpen) {
          wrap.classList.remove("is-dismissed");
          wrap.classList.add("is-open");
          button.setAttribute("aria-expanded", "true");
        }
      });
      button.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;
        event.preventDefault();
        closeHelpTips();
      });
      button.addEventListener("blur", function () { wrap.classList.remove("is-dismissed"); });
      wrap.addEventListener("pointerleave", function () { wrap.classList.remove("is-dismissed"); });
    });
    document.addEventListener("click", closeHelpTips);
  }
  function nodeCenter(node) {
    return { x: node.x + 9, y: node.y + 8 };
  }

  function drawGraph(scenario) {
    var stage = byId("lineage-stage");
    var svg = '<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">';
    scenario.edges.forEach(function (edge, index) {
      var start = scenario.nodes.find(function (node) { return node.id === edge[0]; });
      var end = scenario.nodes.find(function (node) { return node.id === edge[1]; });
      var a = nodeCenter(start); var b = nodeCenter(end);
      svg += '<path class="edge ' + (index > 1 ? "downstream" : "") + '" data-edge="' + index + '" d="M ' + a.x + " " + a.y + " C " + ((a.x + b.x) / 2) + " " + a.y + ", " + ((a.x + b.x) / 2) + " " + b.y + ", " + b.x + " " + b.y + '"/>';
    });
    svg += "</svg>";
    stage.innerHTML = svg + scenario.nodes.map(function (node, index) {
      return '<button type="button" class="graph-node ' + escapeHTML(node.kind) + '" data-node="' + escapeHTML(node.id) + '" style="left:' + node.x + "%;top:" + node.y + '%" aria-label="Inspect ' + escapeHTML(node.label) + '"><span><i></i>' + escapeHTML(node.label) + "</span><small>" + escapeHTML(node.detail) + "</small></button>";
    }).join("");
    all(".graph-node").forEach(function (button, index) {
      button.addEventListener("click", function () { inspectNode(scenario.nodes[index], index); });
    });
    inspectNode(scenario.nodes[0], 0);
  }

  function inspectNode(node, index) {
    all(".graph-node").forEach(function (button) { button.classList.toggle("is-selected", button.dataset.node === node.id); });
    var inspector = byId("node-inspector");
    inspector.innerHTML = '<span class="inspector-icon">' + (index + 1) + '</span><div><small>Selected evidence</small><strong>' + escapeHTML(node.label) + "</strong><p>" + escapeHTML(node.text) + "</p></div>";
  }

  function selectScenario(name, shouldScroll) {
    if (!scenarios[name]) return;
    resetDemo(false);
    selected = name;
    var scenario = scenarios[name];
    all(".preset-card").forEach(function (card) {
      var active = card.dataset.scenario === name;
      card.classList.toggle("is-selected", active);
      card.setAttribute("aria-pressed", String(active));
    });
    byId("workspace-title").textContent = scenario.title;
    byId("workspace-subtitle").textContent = scenario.subtitle;
    byId("finding-copy").textContent = scenario.copy;
    byId("evidence-heading").textContent = scenario.finding;
    byId("query-code").textContent = scenario.query;
    byId("proposal-risk").textContent = scenario.proposal;
    byId("proposal-k").textContent = scenario.k;
    drawGraph(scenario);
    hydrateScenario(name);
    hydrateCodegen(name);
    if (shouldScroll) {
      if (history.replaceState) history.replaceState(null, "", "?case=" + name);
      byId("workspace").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function updateNarrator(index) {
    var item = narration[index];
    if (selected === "control" && index >= 1) {
      var control = [
        null,
        { kicker: "Step 2 - Screen", title: "No person-joinable combination exists.", body: "The operational run ID is high-cardinality, but its meaning and lineage do not connect it to a person.", why: "Mosaic refuses to equate many distinct values with compositional privacy risk." },
        { kicker: "Step 3 - Stop safely", title: "No data query is needed.", body: "Because the metadata screen found no multi-family convergence, Mosaic does not issue an aggregate query.", why: "Failing closed also means avoiding unnecessary data access." },
        { kicker: "Step 4 - Defend", title: "The safety boundary is tested anyway.", body: "Hostile catalog text still cannot open a row-level data path.", why: "A negative privacy finding never disables the agent's deterministic query policy." },
        { kicker: "Step 5 - Verify control", title: "The negative control stays clear.", body: "No mitigation is recommended because Mosaic has not manufactured a risk finding.", why: "Safe controls demonstrate that the product distinguishes signal from cardinality theater." },
        { kicker: "Step 6 - Record", title: "Keep the clear decision without raising an incident.", body: "The evidence records why the candidate was rejected and proposes no catalog mutation.", why: "Future reviewers inherit the reasoning as well as the outcome." }
      ];
      item = control[index];
    }
    if (selected === "mitigated") {
      item = [
        { kicker: "Step 1 - Discover", title: "Read the original and shadow lineage.", body: "DataHub connects the precise export to a reversible candidate that suppresses birth date.", why: "The source remains unchanged while Mosaic evaluates a safer release." },
        { kicker: "Step 2 - Compare", title: "Hold the useful context constant.", body: "The candidate keeps ZIP5 and demographic category while removing the most precise date field.", why: "A mitigation should reduce risk without destroying analytical value." },
        { kicker: "Step 3 - Validate", title: "Measure whether the candidate actually works.", body: "Aggregate counts show minimum anonymity improving from k=1 to k=20.", why: "Mosaic verifies the outcome instead of treating a transformation name as proof." },
        { kicker: "Step 4 - Defend", title: "Keep the same safety boundary.", body: "Hostile metadata still cannot request raw identifiers from the safer candidate.", why: "Mitigation never relaxes the deterministic query policy." },
        { kicker: "Step 5 - Preserve utility", title: "Choose the smallest effective change.", body: "Suppression clears the visible threshold while retaining 76% analytical utility.", why: "Teams receive a usable release, not a blanket denial." },
        { kicker: "Step 6 - Generate", title: "Generate the verified safer model.", body: "Mosaic emits the dbt transformation, aggregate test, policy, manifest, and review summary.", why: "The measured mitigation becomes a reviewable engineering change." }
      ][index];
    }
    if (selected === "audience") {
      item = [
        { kicker: "Step 1 - Discover", title: "Read lineage across a second business domain.", body: "DataHub maps CRM geography and household context to product age and device cohorts.", why: "The same privacy mechanism can exist outside a research export." },
        { kicker: "Step 2 - Converge", title: "See four audience attributes meet.", body: "Geography, age band, household segment, and device cohort converge before partner delivery.", why: "Neither source exposes the complete identifying combination alone." },
        { kicker: "Step 3 - Validate", title: "Prove the audience contains small groups.", body: "Aggregate validation finds k=1 and 44.444% of records below k=5.", why: "The verdict comes from measured groups, not a marketing-data stereotype." },
        { kicker: "Step 4 - Defend", title: "Reject row-level extraction again.", body: "Adversarial catalog text cannot turn the audience investigation into an identity export.", why: "The safety boundary generalizes with the detection mechanism." },
        { kicker: "Step 5 - Mitigate", title: "Compare reversible audience reductions.", body: "Mosaic evaluates which precise segment can be suppressed or generalized before delivery.", why: "The response can preserve campaign utility while reducing exposure." },
        { kicker: "Step 6 - Generate", title: "Turn the audience proof into reviewed code.", body: "The generated bundle carries the DataHub URN, aggregate test, policy, and provenance.", why: "A second domain produces the same auditable engineering workflow." }
      ][index];
    }    byId("narrator").classList.remove("is-complete");
    byId("narrator-step").textContent = "Step " + (index + 1) + " of 6";
    byId("narrator-kicker").textContent = item.kicker;
    byId("narrator-title").textContent = item.title;
    byId("narrator-body").textContent = item.body;
    byId("narrator-why").textContent = item.why;
  }

  function completeNarrator(scenario) {
    byId("narrator").classList.add("is-complete");
    byId("narrator-step").textContent = "Complete";
    byId("narrator-kicker").textContent = "What this proves";
    byId("narrator-title").textContent = scenario.verdict === "Critical" ? "The graph exposed a measurable risk and a safer path." : "Mosaic reached the right decision without exposing a person.";
    byId("narrator-body").textContent = scenario.copy;
    byId("narrator-why").textContent = "Choose the attack replay or inspect the generated change. The page will not move you without permission.";
    byId("narrator-actions").hidden = false;
    byId("advance-demo-step").hidden = true;
    byId("review-attack").hidden = false;
    byId("review-pr").hidden = scenario.verdict === "Clear";
    byId("review-tour").hidden = !tourRunning;
    byId("narrator").focus({ preventScroll: true });
  }
  function resetNarrator() {
    byId("narrator").classList.remove("is-complete");
    byId("narrator-step").textContent = "Before you run";
    byId("narrator-kicker").textContent = "The whole idea";
    byId("narrator-title").textContent = "DataHub shows the combination. Mosaic proves whether it is risky.";
    byId("narrator-body").textContent = "Press Start selected demo to reveal step 1. We will explain each catalog read, calculation, safety guardrail, and proposed action, one evidence step per click.";
    byId("narrator-why").textContent = "The agent receives metadata and group counts - never a person-level row.";
    byId("narrator-actions").hidden = true;
    byId("advance-demo-step").hidden = true;
    byId("review-attack").hidden = true;
    byId("review-pr").hidden = true;
    byId("review-tour").hidden = true;
  }
  function setProgress(index) {
    all(".run-progress li").forEach(function (item, itemIndex) {
      item.classList.toggle("is-active", itemIndex === index);
      item.classList.toggle("is-done", itemIndex < index);
    });
    all(".edge").forEach(function (edge, edgeIndex) { edge.classList.toggle("is-lit", edgeIndex <= index); });
  }

  function addLog(message) {
    var log = byId("activity-log");
    var empty = log.querySelector(".empty-log");
    if (empty) empty.remove();
    var elapsed = ((performance.now() - startedAt) / 1000).toFixed(1).padStart(4, "0");
    var item = document.createElement("li");
    item.innerHTML = "<time>+" + elapsed + "s</time><i></i><span>" + escapeHTML(message) + "</span>";
    log.appendChild(item);
  }

  function setFinding(scenario) {
    byId("finding-title").textContent = scenario.finding;
    var verdict = byId("finding-verdict");
    verdict.textContent = scenario.verdict;
    verdict.className = "verdict " + scenario.verdictClass;
    byId("metric-k").textContent = scenario.k === "N/A" ? "N/A" : "k=" + scenario.k;
    byId("metric-k-note").textContent = scenario.k === "N/A" ? "No risky convergence to measure" : "Smallest equivalence class";
    byId("metric-below").textContent = scenario.below + "%";
    byId("metric-downstream").textContent = String(scenario.downstream);
    byId("finding-callout").innerHTML = '<span></span><p><strong>' + escapeHTML(scenario.verdict) + ".</strong> " + escapeHTML(scenario.copy) + "</p>";
  }

  function updateClock() {
    var elapsed = (performance.now() - startedAt) / 1000;
    byId("elapsed").textContent = "00:" + elapsed.toFixed(1).padStart(4, "0");
  }

  function resetAttackLab() {
    all("[data-attack-stage]").forEach(function (stage) { stage.classList.remove("is-live", "is-refused"); });
    byId("attack-verdict").textContent = "Ready to challenge";
    byId("attack-reason").textContent = "No request has been evaluated yet.";
    byId("attack-continuation").textContent = "Ready";
    byId("run-attack").disabled = false;
    byId("run-attack").textContent = "Replay attack";
  }

  function runAttackLab(shouldScroll) {
    if (attackController) attackController.abort();
    var requestId = ++attackRequestId;
    var controller = new AbortController();
    attackController = controller;
    var timeoutId = setTimeout(function () { controller.abort(); }, 4_000);
    byId("tab-button-attack").click();
    if (shouldScroll) byId("tab-attack").scrollIntoView({ behavior: "smooth", block: "center" });
    resetAttackLab();
    byId("run-attack").disabled = true;
    byId("run-attack").textContent = "Checking policy...";
    var stages = all("[data-attack-stage]");
    stages[0].classList.add("is-live");
    stages[1].classList.add("is-live");
    byId("advance-demo-step").disabled = true;
    return fetch("/api/redteam", { signal: controller.signal })
      .then(function (response) { if (!response.ok) throw new Error("red-team unavailable"); return response.json(); })
      .then(function (receipt) {
        clearTimeout(timeoutId);
        if (requestId !== attackRequestId) return;
        if (attackController === controller) attackController = null;
        stages[2].classList.add("is-live", "is-refused");
        byId("attack-verdict").textContent = receipt.controls.policy_refused_requested_sql ? "REFUSED · zero rows" : "FAILED OPEN";
        byId("attack-reason").textContent = receipt.controls.denial_reason || receipt.failure_condition;
        byId("attack-rows").textContent = receipt.controls.raw_person_rows_returned;
        byId("attack-mutations").textContent = receipt.controls.mutation_performed ? "1" : "0";
        byId("attack-continuation").textContent = receipt.controls.run_continued_with_policy_compiled_aggregate ? "Continued" : "Stopped";
        byId("run-attack").disabled = false;
        byId("run-attack").textContent = "Replay attack";
        byId("advance-demo-step").disabled = false;
      })
      .catch(function (error) {
        clearTimeout(timeoutId);
        if (requestId !== attackRequestId) return;
        if (attackController === controller) attackController = null;
        byId("attack-verdict").textContent = error.name === "AbortError" ? "Timed out safely" : "Receipt unavailable";
        byId("attack-reason").textContent = "The receipt could not be loaded. The demo stayed aggregate-only and did not advance.";
        byId("run-attack").disabled = false;
        byId("run-attack").textContent = "Retry attack";
        byId("advance-demo-step").disabled = false;
      });
  }
  function setCaseNavigationDisabled(disabled) {
    all(".preset-card, [data-tour-scenario]").forEach(function (button) {
      button.disabled = disabled;
    });
    byId("next-tour-case").disabled = disabled || byId("next-tour-case").dataset.ready !== "true";
  }

  function resetTourUI() {
    all("[data-tour-scenario]").forEach(function (button) {
      button.classList.remove("is-active", "is-done");
      button.setAttribute("aria-pressed", "false");
      button.querySelector("small").textContent = "Waiting";
    });
    all("[data-tour-result]").forEach(function (card) {
      card.classList.remove("is-verified");
      card.querySelector("small").textContent = "Waiting to run";
    });
    byId("tour-summary").hidden = true;
    byId("review-tour").hidden = true;
    byId("compare-tour").hidden = true;
    byId("next-tour-case").disabled = true;
    byId("next-tour-case").dataset.ready = "false";
    byId("next-tour-case").textContent = "Next case";
  }

  function chooseTourScenario(name, shouldScroll) {
    if (!scenarios[name]) return;
    if (running) {
      showToast("Let this case finish or reset it before choosing another.");
      return;
    }
    tourIndex = tourOrder.indexOf(name);
    selectScenario(name, false);
    all("[data-tour-scenario]").forEach(function (button) {
      var active = button.dataset.tourScenario === name;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
      if (active && !button.classList.contains("is-done")) {
        button.querySelector("small").textContent = "Selected";
      } else if (!active && !button.classList.contains("is-done")) {
        button.querySelector("small").textContent = "Waiting";
      }
    });
    byId("tour-title").textContent = "Case " + (tourIndex + 1) + " of 4: " + scenarios[name].title;
    byId("tour-copy").textContent = scenarios[name].subtitle + " Nothing runs until you press Start selected case.";
    byId("run-tour-case").disabled = false;
    byId("run-tour-case").textContent = document.querySelector('[data-tour-result="' + name + '"]').classList.contains("is-verified") ? "Run this case again" : "Start selected case";
    var alreadyRun = document.querySelector('[data-tour-result="' + name + '"]').classList.contains("is-verified");
    byId("next-tour-case").dataset.ready = String(alreadyRun);
    byId("next-tour-case").disabled = !alreadyRun;
    if (shouldScroll) byId("workspace").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function beginTour() {
    if (running) {
      showToast("Finish or reset the current investigation before opening the case explorer.");
      return;
    }
    tourRunning = true;
    resetTourUI();
    byId("tour-controller").hidden = false;
    byId("run-all-scenarios").textContent = "Restart case explorer";
    chooseTourScenario(selected, false);
    byId("workspace").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function runSelectedTourCase() {
    if (running) {
      showToast("Use Continue below to reveal the next evidence step.");
      return;
    }
    if (!tourRunning) {
      setCaseNavigationDisabled(true);
      runDemo(function () { setCaseNavigationDisabled(false); });
      return;
    }
    var name = selected;
    var item = document.querySelector('[data-tour-scenario="' + name + '"]');
    item.classList.add("is-active");
    item.querySelector("small").textContent = "Running";
    byId("tour-title").textContent = "Running case " + (tourIndex + 1) + " of 4: " + scenarios[name].title;
    byId("tour-copy").textContent = "Step 1 appears now. Every later evidence step waits for your click.";
    setCaseNavigationDisabled(true);
    runDemo(function () { completeTourScenario(name); });
  }
  function completeTourScenario(name) {
    if (!tourRunning) return;
    var scenario = scenarios[name];
    var item = document.querySelector('[data-tour-scenario="' + name + '"]');
    var result = document.querySelector('[data-tour-result="' + name + '"]');
    item.classList.remove("is-active");
    item.classList.add("is-done");
    item.setAttribute("aria-pressed", "true");
    item.querySelector("small").textContent = scenario.verdict;
    result.classList.add("is-verified");
    result.querySelector("small").textContent = scenario.k === "N/A" ? "Verified clear / no data query" : "Verified " + scenario.verdict + " / k=" + scenario.k;
    setCaseNavigationDisabled(false);
    byId("run-tour-case").disabled = false;
    byId("run-tour-case").textContent = "Run this case again";
    byId("next-tour-case").dataset.ready = "true";
    byId("next-tour-case").disabled = false;
    byId("compare-tour").hidden = false;
    byId("review-tour").hidden = false;
    var completed = all("[data-tour-result].is-verified").length;
    byId("tour-title").textContent = scenario.title + " complete. Pause and inspect the evidence.";
    byId("tour-copy").textContent = completed + " of 4 cases verified. Move next only when you are ready.";
    if (completed === tourOrder.length) {
      byId("tour-title").textContent = "All four cases verified - on your schedule.";
      byId("tour-copy").textContent = "Two risks detected, one mitigation validated, one false positive refused, and zero person-level rows returned.";
      byId("next-tour-case").disabled = true;
      byId("next-tour-case").dataset.ready = "false";
      byId("run-all-scenarios").textContent = "Review all 4 again";
      showToast("All four cases are complete. Compare them whenever you are ready.");
    } else {
      showToast("Case complete. Inspect it, choose another case, or compare completed results.");
    }
  }

  function nextTourScenario() {
    if (running) return;
    var nextName = null;
    for (var offset = 1; offset <= tourOrder.length; offset += 1) {
      var candidate = tourOrder[(tourIndex + offset) % tourOrder.length];
      if (!document.querySelector('[data-tour-result="' + candidate + '"]').classList.contains("is-verified")) {
        nextName = candidate;
        break;
      }
    }
    if (!nextName) {
      showTourSummary();
      return;
    }
    chooseTourScenario(nextName, false);
  }

  function showTourSummary() {
    var completed = all("[data-tour-result].is-verified").length;
    if (!completed) {
      showToast("Run at least one case before comparing results.");
      return;
    }
    byId("tour-summary").hidden = false;
    byId("tour-summary-title").textContent = completed === 4 ? "Four cases. Four evidence-based decisions." : completed + " of 4 cases compared so far.";
    byId("tour-summary").focus({ preventScroll: true });
    var reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    byId("tour-summary").scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  }

  function cancelTour(showMessage) {
    if (!tourRunning) return;
    tourRunning = false;
    resetDemo(false);
    setCaseNavigationDisabled(false);
    byId("tour-controller").hidden = true;
    if (showMessage) showToast("Case explorer closed. Choose any case to continue individually.");
  }

  function openCasePicker() {
    byId("presets").scrollIntoView({ behavior: "smooth", block: "start" });
    var active = document.querySelector(".preset-card.is-selected") || document.querySelector(".preset-card");
    if (active) active.focus({ preventScroll: true });
  }

  function resetSelectedCase() {
    resetDemo(true);
    setCaseNavigationDisabled(false);
    if (tourRunning) chooseTourScenario(selected, false);
  }
  function messagesForScenario(name) {
    if (name === "control") return [
      "Read field semantics and column lineage from DataHub.",
      "No multi-family person-joinable convergence found.",
      "Skipped aggregate query: candidate failed the metadata screen.",
      "Replayed hostile catalog metadata; row-level request refused.",
      "Confirmed safe negative control; no mitigation required.",
      "Recorded clear decision; no catalog mutation proposed."
    ];
    if (name === "mitigated") return [
      "Read original and shadow-model lineage from DataHub.",
      "Held ZIP5 and demographic context constant; suppressed precise birth date.",
      "Executed allowlisted GROUP BY; verified k improves from 1 to 20.",
      "Replayed hostile metadata; row-level request refused.",
      "Confirmed 76% utility retained after the smallest effective change.",
      "Generated the verified safer model and aggregate regression test."
    ];
    if (name === "audience") return [
      "Read CRM and product-analytics column lineage from DataHub.",
      "Mapped geography, age, household, and device families before partner delivery.",
      "Executed allowlisted GROUP BY; found k=1 with 44.444% below k=5.",
      "Replayed hostile metadata; identity-export request refused.",
      "Compared reversible audience suppression and generalization options.",
      "Generated a DataHub-grounded audience remediation bundle."
    ];
    return [
      "Read 3 column-lineage paths from DataHub.",
      "Mapped location, date-of-birth, and demographic families.",
      "Executed allowlisted GROUP BY; received counts only.",
      "Replayed hostile DataHub description; policy refused raw identifiers.",
      "Compared 3 reversible mitigations; suppression retains 76% utility.",
      "Generated 6 merge-ready artifacts; awaiting reviewer approval."
    ];
  }

  function setStepControlLabel(label) {
    byId("narrator-actions").hidden = false;
    byId("advance-demo-step").hidden = false;
    byId("advance-demo-step").disabled = false;
    byId("advance-demo-step").textContent = label;
  }

  function finishDemo() {
    var scenario = runScenario;
    all(".run-progress li").forEach(function (item) {
      item.classList.add("is-done");
      item.classList.remove("is-active");
    });
    updateClock();
    running = false;
    byId("run-demo").disabled = false;
    byId("run-demo").querySelector(".run-label").textContent = "Run again";
    completeNarrator(scenario);
    if (selected !== "control") {
      showToast("Investigation complete. Choose what to inspect next.");
    } else {
      showToast("Safe control complete. Mosaic correctly generated no remediation code.");
    }
    var completion = runCompletion;
    runMessages = [];
    runStep = -1;
    runScenario = null;
    runCompletion = null;
    if (typeof completion === "function") completion();
  }

  function advanceDemoStep() {
    if (!running || !runScenario || byId("advance-demo-step").disabled) return;
    runStep += 1;
    var index = runStep;
    var message = runMessages[index];
    setProgress(index);
    updateNarrator(index);
    addLog(message);
    updateClock();
    if (index === 2) {
      setFinding(runScenario);
      byId("tab-button-query").click();
    }
    if (index === 4 && selected !== "control") byId("tab-button-mitigation").click();
    if (index === 5 && selected !== "control") byId("tab-button-codegen").click();

    if (index < runMessages.length - 1) {
      var nextStep = index + 2;
      setStepControlLabel("Continue to step " + nextStep + " of " + runMessages.length);
      if (tourRunning) {
        byId("tour-copy").textContent = "Step " + (index + 1) + " of 6 is open. Nothing else happens until you press Continue.";
      }
      if (index === 3) runAttackLab(false);
      return;
    }
    finishDemo();
  }

  function runDemo(onComplete) {
    resetDemo(false);
    running = true;
    startedAt = performance.now();
    runScenario = scenarios[selected];
    runMessages = messagesForScenario(selected);
    runStep = -1;
    runCompletion = onComplete;
    byId("run-demo").disabled = true;
    byId("run-demo").querySelector(".run-label").textContent = "Case in progress";
    byId("run-tour-case").disabled = true;
    if (tourRunning) byId("run-tour-case").textContent = "Case in progress";
    advanceDemoStep();
  }
  function resetDemo(clearScenario) {
    runMessages = [];
    runStep = -1;
    runScenario = null;
    runCompletion = null;
    if (attackController) attackController.abort();
    attackController = null;
    attackRequestId += 1;
    running = false;
    all(".run-progress li").forEach(function (item) { item.classList.remove("is-active", "is-done"); });
    all(".edge").forEach(function (edge) { edge.classList.remove("is-lit"); });
    byId("finding-title").textContent = "Waiting to run";
    byId("finding-verdict").textContent = "Ready";
    byId("finding-verdict").className = "verdict neutral";
    byId("metric-k").textContent = "--"; byId("metric-below").textContent = "--"; byId("metric-downstream").textContent = "--";
    byId("metric-k-note").textContent = "Run validation to calculate";
    byId("finding-callout").innerHTML = '<span></span><p>Select <strong>Start selected demo</strong> to reveal the first evidence step.</p>';
    byId("activity-log").innerHTML = '<li class="empty-log">No actions yet. Start the selected demo above.</li>';
    byId("elapsed").textContent = "00:00.0";
    resetNarrator();
    resetAttackLab();
    byId("run-demo").hidden = tourRunning;
    byId("run-demo").disabled = false;
    byId("run-demo").querySelector(".run-label").textContent = "Start selected demo";
    byId("run-tour-case").disabled = false;
    byId("run-tour-case").textContent = "Start selected case";
    byId("advance-demo-step").disabled = false;
    if (clearScenario) drawGraph(scenarios[selected]);
  }
  function showToast(message) {
    var toast = byId("toast");
    toast.textContent = message; toast.hidden = false;
    setTimeout(function () { toast.hidden = true; }, 3500);
  }

  function initTabs() {
    all("[data-tab]").forEach(function (button) {
      button.addEventListener("click", function () {
        all("[data-tab]").forEach(function (candidate) { candidate.setAttribute("aria-selected", String(candidate === button)); });
        all(".tab-content").forEach(function (panel) { panel.hidden = panel.id !== "tab-" + button.dataset.tab; });
      });
    });
  }

  function showGeneratedArtifact(bundle, index) {
    var artifact = bundle.artifacts[index];
    if (!artifact) return;
    byId("generated-path").textContent = artifact.path;
    byId("generated-code").textContent = artifact.content;
    all(".generated-file").forEach(function (button) {
      button.classList.toggle("is-active", Number(button.dataset.artifactIndex) === index);
    });
  }

  function renderCodegenBundle(bundle) {
    var list = byId("generated-file-list");
    var preferredIndex = bundle.artifacts.findIndex(function (artifact) { return artifact.path.indexOf("models/") === 0 && artifact.path.endsWith(".sql"); });
    if (preferredIndex < 0) preferredIndex = bundle.artifacts.findIndex(function (artifact) { return artifact.path === "PR_SUMMARY.md"; });
    if (preferredIndex < 0) preferredIndex = 0;
    list.innerHTML = "";
    bundle.artifacts.forEach(function (artifact, index) {
      var button = document.createElement("button");
      var extension = artifact.path.split(".").pop().toUpperCase();
      button.type = "button";
      button.className = "generated-file" + (index === preferredIndex ? " is-active" : "");
      button.dataset.artifactIndex = String(index);
      button.innerHTML = "<span>" + escapeHTML(extension) + "</span><b>" + escapeHTML(artifact.path) + "</b>";
      button.addEventListener("click", function () { showGeneratedArtifact(bundle, index); });
      list.appendChild(button);
    });
    byId("codegen-status").textContent = bundle.validation.checks.length + " checks passed";
    byId("codegen-sha").textContent = "bundle sha256: " + bundle.bundle_sha256.slice(0, 20) + "...";
    byId("codegen-receipt").textContent = bundle.strategy;
    var download = byId("codegen-download");
    download.href = "/api/remediation-bundles/" + encodeURIComponent(bundle.scenario) + "/download";
    download.removeAttribute("aria-disabled");
    byId("codegen-impact").hidden = false;
    showGeneratedArtifact(bundle, preferredIndex);
  }

  function renderNoCodegen(message) {
    byId("generated-file-list").innerHTML = '<div class="no-generation">No files generated</div>';
    byId("generated-path").textContent = "generation-refused.txt";
    byId("generated-code").textContent = message;
    byId("codegen-status").textContent = "Stopped safely";
    byId("codegen-sha").textContent = "No bundle digest: no candidate existed.";
    byId("codegen-receipt").textContent = "Mosaic refuses to manufacture code for a safe control.";
    byId("codegen-impact").hidden = true;
    var download = byId("codegen-download");
    download.removeAttribute("href");
    download.setAttribute("aria-disabled", "true");
  }

  function hydrateCodegen(name) {
    var requestId = ++codegenRequestId;
    if (name === "control") {
      renderNoCodegen("Metadata screening found no compositional privacy risk. No remediation is necessary, so Mosaic generated no code.");
      return;
    }
    byId("generated-code").textContent = "Generating from DataHub context...";
    fetch("/api/remediation-bundles/" + encodeURIComponent(name))
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (bundle) {
        if (requestId === codegenRequestId && selected === name) renderCodegenBundle(bundle);
      })
      .catch(function () {
        if (requestId === codegenRequestId && selected === name) {
          renderNoCodegen("The generator API is temporarily unavailable. Use the committed examples or run the CLI locally.");
        }
      });
  }
  function hydrateScenario(name) {
    fetch("/api/scenarios/" + encodeURIComponent(name))
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (report) {
        var assessment = report.assessment;
        var metrics = assessment.metrics;
        var scenario = scenarios[name];
        if (!scenario) return;
        scenario.k = metrics ? metrics.minimum_k : "N/A";
        scenario.below = metrics ? metrics.percent_below_5 : 0;
        scenario.downstream = assessment.candidate.downstream_assets.length;
        scenario.proposal = assessment.verdict;
        if (assessment.aggregate_query) {
          scenario.query = assessment.aggregate_query
            .replace(" FROM ", "\nFROM ")
            .replace(" GROUP BY ", "\nGROUP BY ");
        }
        if (selected === name) {
          byId("query-code").textContent = scenario.query;
          byId("proposal-risk").textContent = scenario.proposal;
          byId("proposal-k").textContent = scenario.k;
        }
      })
      .catch(function () {
        showToast("Using bundled scenario evidence; the scenario API is temporarily unavailable.");
      });
  }
  function hydrateLiveEvidence() {
    Promise.all([fetch("/api/assessment").then(function (response) { return response.json(); }), fetch("/api/mitigations").then(function (response) { return response.json(); })])
      .then(function (reports) {
        var assessment = reports[0].assessment;
        scenarios.research.k = assessment.metrics.minimum_k;
        scenarios.research.below = assessment.metrics.percent_below_5;
        scenarios.research.downstream = assessment.candidate.downstream_assets.length;
        scenarios.research.query = assessment.aggregate_query.replace(" FROM ", "\nFROM ").replace(" GROUP BY ", "\nGROUP BY ");
        var recommendation = reports[1].recommended;
        if (recommendation) scenarios.mitigated.k = recommendation.minimum_k;
        if (selected === "research") {
          byId("query-code").textContent = scenarios.research.query;
          byId("proposal-k").textContent = scenarios.research.k;
        }
      })
      .catch(function () { showToast("Using bundled deterministic evidence; the API is temporarily unavailable."); });
  }

  function shortAsset(urn) {
    var match = urn.match(/,([^,]+),PROD\)$/);
    return match ? match[1].replace(/_/g, " ") : urn;
  }

  function hydrateCrossAssetEvidence() {
    fetch("/api/scan")
      .then(function (response) { if (!response.ok) throw new Error("scan unavailable"); return response.json(); })
      .then(function (scan) {
        var finding = scan.cross_asset_findings && scan.cross_asset_findings[0];
        byId("cross-asset-count").textContent = scan.cross_asset_candidates || 0;
        if (!finding) {
          byId("cross-left").textContent = "No unsupported claim";
          byId("cross-right").textContent = "No candidate invented";
          byId("cross-key").textContent = "none";
          byId("cross-reason").textContent = "No pair met the deterministic rule: shared join key plus distinct contributed families.";
          return;
        }
        byId("cross-left").textContent = shortAsset(finding.left_asset_urn);
        byId("cross-right").textContent = shortAsset(finding.right_asset_urn);
        byId("cross-key").textContent = finding.shared_join_keys.join(", ");
        var midpoint = Math.max(1, Math.floor(finding.combined_families.length / 2));
        byId("cross-left-family").textContent = finding.combined_families.slice(0, midpoint).join(" + ");
        byId("cross-right-family").textContent = finding.combined_families.slice(midpoint).join(" + ");
        byId("cross-reason").textContent = finding.decision_reason;
      })
      .catch(function () { byId("cross-reason").textContent = "Estate scan unavailable. Inspect the CLI output locally with: mosaic scan"; });
  }

  function hydrateAgentReceipts() {
    fetch("/api/agent-receipts")
      .then(function (response) { if (!response.ok) throw new Error("receipt unavailable"); return response.json(); })
      .then(function (payload) {
        var accepted = payload.receipts.find(function (item) { return item.status === "accepted_for_human_review"; });
        var vetoes = payload.receipts.filter(function (item) { return item.status === "vetoed"; });
        byId("agent-veto-count").textContent = vetoes.length;
        if (!accepted) throw new Error("accepted receipt unavailable");
        byId("agent-receipt-status").textContent = "Accepted for human review";
        byId("agent-selection").textContent = accepted.proposal.selected_scenario + " / " + accepted.proposal.nominated_columns.join(" + ");
        byId("agent-rationale").textContent = accepted.proposal.rationale;
        byId("agent-policy").textContent = accepted.verification.deterministic_assessment.assessment.verdict.replace(/_/g, " ");
        byId("agent-query").textContent = accepted.verification.compiled_aggregate_query;
      })
      .catch(function () { byId("agent-receipt-status").textContent = "Run locally with mosaic assess --agent"; });
  }

  function hydrateRedteamReceipt() {
    fetch("/api/redteam")
      .then(function (response) { if (!response.ok) throw new Error("red-team unavailable"); return response.json(); })
      .then(function (payload) {
        var refused = payload.controls && payload.controls.policy_refused_requested_sql;
        byId("redteam-status").textContent = refused ? "Refused" : "FAILED";
      })
      .catch(function () { byId("redteam-status").textContent = "Run locally"; });
  }

  function boot() {
    initTheme(); initTabs(); initHelpTips();
    all(".preset-card").forEach(function (card) {
      card.addEventListener("click", function () {
        if (tourRunning) chooseTourScenario(card.dataset.scenario, true);
        else selectScenario(card.dataset.scenario, true);
      });
    });
    all("[data-tour-scenario]").forEach(function (button) {
      button.addEventListener("click", function () { chooseTourScenario(button.dataset.tourScenario, false); });
    });
    byId("run-all-scenarios").addEventListener("click", beginTour);
    byId("run-tour-case").addEventListener("click", runSelectedTourCase);
    byId("advance-demo-step").addEventListener("click", advanceDemoStep);
    byId("next-tour-case").addEventListener("click", nextTourScenario);
    byId("compare-tour").addEventListener("click", showTourSummary);
    byId("cancel-tour").addEventListener("click", function () { cancelTour(true); });
    byId("run-demo").addEventListener("click", runSelectedTourCase);
    byId("run-attack").addEventListener("click", function () { runAttackLab(false); });
    byId("review-attack").addEventListener("click", function () { runAttackLab(true); });
    byId("review-pr").addEventListener("click", function () { byId("tab-button-codegen").click(); byId("tab-codegen").scrollIntoView({ behavior: "smooth", block: "start" }); });
    byId("review-tour").addEventListener("click", showTourSummary);
    byId("reset-demo").addEventListener("click", resetSelectedCase);
    byId("hero-run").addEventListener("click", openCasePicker);
    var requested = new URLSearchParams(location.search).get("case");
    selectScenario(scenarios[requested] ? requested : "research", false);
    hydrateLiveEvidence();
    hydrateCrossAssetEvidence();
    hydrateAgentReceipts();
    hydrateRedteamReceipt();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
