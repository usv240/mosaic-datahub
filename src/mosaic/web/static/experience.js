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
    { kicker: "Step 4 - Mitigate", title: "Test safer versions before changing anything.", body: "A shadow simulation compares suppression and generalization strategies against both privacy and retained utility.", why: "The recommended option lifts k to 20 while retaining the most useful detail." },
    { kicker: "Step 5 - Propose", title: "Generate the fix, behind a human gate.", body: "Mosaic generates a dbt model, aggregate-only test, policy, manifest, and PR summary before preparing DataHub write-back.", why: "A reviewer must approve the code and catalog proposal; Mosaic never commits, merges, or mutates on its own." }
  ];
  var selected = "research";
  var running = false;
  var runTimers = [];
  var startedAt = 0;
  var clockTimer = null;

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
      if (history.replaceState) history.replaceState(null, "", "?case=" + name + "#workspace");
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
        { kicker: "Step 4 - Verify control", title: "The negative control stays clear.", body: "No mitigation is recommended because Mosaic has not manufactured a risk finding.", why: "Safe controls demonstrate that the product distinguishes signal from cardinality theater." },
        { kicker: "Step 5 - Record", title: "Keep the clear decision without raising an incident.", body: "The evidence records why the candidate was rejected and proposes no catalog mutation.", why: "Future reviewers inherit the reasoning as well as the outcome." }
      ];
      item = control[index];
    }
    byId("narrator").classList.remove("is-complete");
    byId("narrator-step").textContent = "Step " + (index + 1) + " of 5";
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
    byId("narrator-why").textContent = "Inspect Finding, Validation query, Mitigation lab, generated Remediation PR, and DataHub proposal below. Every claim has visible evidence.";
  }

  function resetNarrator() {
    byId("narrator").classList.remove("is-complete");
    byId("narrator-step").textContent = "Before you run";
    byId("narrator-kicker").textContent = "The whole idea";
    byId("narrator-title").textContent = "DataHub shows the combination. Mosaic proves whether it is risky.";
    byId("narrator-body").textContent = "Press Run investigation. We will explain each catalog read, calculation, safety guardrail, and proposed action as it happens.";
    byId("narrator-why").textContent = "The agent receives metadata and group counts - never a person-level row.";
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

  function runDemo() {
    if (running) return;
    resetDemo(false);
    running = true;
    startedAt = performance.now();
    var scenario = scenarios[selected];
    var button = byId("run-demo");
    button.disabled = true;
    button.querySelector(".run-label").textContent = "Investigating...";
    clockTimer = setInterval(updateClock, 100);
    var reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
    var delay = reduceMotion ? 25 : 620;
    var messages = selected === "control" ? [
      "Read field semantics and column lineage from DataHub.",
      "No multi-family person-joinable convergence found.",
      "Skipped aggregate query: candidate failed the metadata screen.",
      "Confirmed safe negative control; no mitigation required.",
      "Recorded clear decision; no catalog mutation proposed."
    ] : [
      "Read 3 column-lineage paths from DataHub.",
      "Mapped location, date-of-birth, and demographic families.",
      "Executed allowlisted GROUP BY; received counts only.",
      selected === "mitigated" ? "Confirmed suppression lifts minimum anonymity to k=20." : "Compared 3 reversible mitigations; suppression retains 76% utility.",
      "Generated 6 merge-ready artifacts; awaiting reviewer approval."
    ];
    messages.forEach(function (message, index) {
      runTimers.push(setTimeout(function () {
        setProgress(index);
        updateNarrator(index);
        addLog(message);
        if (index === 2) setFinding(scenario);
        if (index === messages.length - 1) {
          all(".run-progress li").forEach(function (item) { item.classList.add("is-done"); item.classList.remove("is-active"); });
          clearInterval(clockTimer);
          updateClock();
          running = false;
          button.disabled = false;
          button.querySelector(".run-label").textContent = "Run again";
          completeNarrator(scenario);
          if (selected !== "control") {
            byId("tab-button-codegen").click();
            byId("tab-codegen").scrollIntoView({
              behavior: reduceMotion ? "auto" : "smooth",
              block: "start"
            });
            showToast("Remediation PR generated. Review or download all 6 artifacts.");
          } else {
            showToast("Safe control complete. Mosaic correctly generated no remediation code.");
          }
        }
      }, delay * (index + 1)));
    });
  }

  function resetDemo(clearScenario) {
    runTimers.forEach(clearTimeout); runTimers = [];
    if (clockTimer) clearInterval(clockTimer);
    running = false;
    all(".run-progress li").forEach(function (item) { item.classList.remove("is-active", "is-done"); });
    all(".edge").forEach(function (edge) { edge.classList.remove("is-lit"); });
    byId("finding-title").textContent = "Waiting to run";
    byId("finding-verdict").textContent = "Ready";
    byId("finding-verdict").className = "verdict neutral";
    byId("metric-k").textContent = "--"; byId("metric-below").textContent = "--"; byId("metric-downstream").textContent = "--";
    byId("metric-k-note").textContent = "Run validation to calculate";
    byId("finding-callout").innerHTML = '<span></span><p>Select <strong>Run investigation</strong> to replay every evidence-producing step.</p>';
    byId("activity-log").innerHTML = '<li class="empty-log">No actions yet. Start the guided replay above.</li>';
    byId("elapsed").textContent = "00:00.0";
    resetNarrator();
    byId("run-demo").disabled = false;
    byId("run-demo").querySelector(".run-label").textContent = "Run investigation";
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
    list.innerHTML = "";
    bundle.artifacts.forEach(function (artifact, index) {
      var button = document.createElement("button");
      var extension = artifact.path.split(".").pop().toUpperCase();
      button.type = "button";
      button.className = "generated-file" + (index === 0 ? " is-active" : "");
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
    showGeneratedArtifact(bundle, 0);
  }

  function renderNoCodegen(message) {
    byId("generated-file-list").innerHTML = '<div class="no-generation">No files generated</div>';
    byId("generated-path").textContent = "generation-refused.txt";
    byId("generated-code").textContent = message;
    byId("codegen-status").textContent = "Stopped safely";
    byId("codegen-sha").textContent = "No bundle digest: no candidate existed.";
    byId("codegen-receipt").textContent = "Mosaic refuses to manufacture code for a safe control.";
    var download = byId("codegen-download");
    download.removeAttribute("href");
    download.setAttribute("aria-disabled", "true");
  }

  function hydrateCodegen(name) {
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
        if (selected === name) renderCodegenBundle(bundle);
      })
      .catch(function () {
        renderNoCodegen("The generator API is temporarily unavailable. Use the committed examples or run the CLI locally.");
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
        if (selected === "research") selectScenario("research", false);
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

  function boot() {
    initTheme(); initTabs();
    all(".preset-card").forEach(function (card) { card.addEventListener("click", function () { selectScenario(card.dataset.scenario, true); }); });
    byId("run-demo").addEventListener("click", runDemo);
    byId("reset-demo").addEventListener("click", function () { resetDemo(true); });
    byId("hero-run").addEventListener("click", function () { selectScenario("research", true); setTimeout(runDemo, 550); });
    var requested = new URLSearchParams(location.search).get("case");
    selectScenario(scenarios[requested] ? requested : "research", false);
    hydrateLiveEvidence();
    hydrateCrossAssetEvidence();
    hydrateAgentReceipts();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
