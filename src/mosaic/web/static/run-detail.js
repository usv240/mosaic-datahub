(function () {
  "use strict";
  const id = (value) => document.getElementById(value);
  const runId = decodeURIComponent(location.pathname.split("/").pop());
  const text = (value) => String(value == null ? "—" : value);
  const escape = (value) => text(value).replace(/[&<>\"]/g, (character) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[character]);
  const row = (term, value) => `<div><dt>${escape(term)}</dt><dd>${escape(value)}</dd></div>`;
  id("print-run").addEventListener("click", () => window.print());
  fetch(`/api/runs/${encodeURIComponent(runId)}`).then((response) => {
    if (!response.ok) throw new Error("not found");
    return response.json();
  }).then((report) => {
    const assessment = report.assessment;
    const metrics = assessment.metrics;
    id("run-title").textContent = report.scenario?.name || "Mosaic assessment";
    id("run-situation").textContent = report.scenario?.situation || "Retained privacy evidence";
    id("integrity").textContent = report.integrity.status === "verified" ? "✓ SHA-256 integrity verified" : "⚠ Integrity verification failed";
    id("integrity").dataset.status = report.integrity.status;
    id("verdict").textContent = assessment.verdict.replaceAll("_", " ");
    id("minimum-k").textContent = metrics ? `k=${metrics.minimum_k}` : "Not queried";
    id("below-five").textContent = metrics ? `${metrics.percent_below_5}%` : "Not queried";
    id("raw-rows").textContent = assessment.raw_rows_returned;
    id("reasons").innerHTML = assessment.reasons.map((reason) => `<li>${escape(reason)}</li>`).join("");
    const graph = report.graph_value;
    id("graph").innerHTML = row("Lineage-aware findings", graph.lineage_aware_convergences) + row("Without lineage", graph.no_lineage_baseline_convergences) + row("Source systems", (graph.source_systems || []).join(", "));
    id("query").textContent = assessment.aggregate_query || "No query issued: metadata screening was sufficient.";
    const mitigation = assessment.mitigation;
    id("mitigation").innerHTML = mitigation ? `<p><strong>${escape(mitigation.action)}</strong></p><p>${escape(mitigation.owner || "Owner assigned in DataHub")}</p>` : "<p>No mitigation required for this control.</p>";
    id("provenance").innerHTML = row("Run ID", report.run_id) + row("Recorded at", report.recorded_at) + row("Configuration SHA-256", report.scenario?.configuration_sha256) + row("Evidence SHA-256", report.sha256) + row("Source", report.source?.kind);
    id("download").href = `/api/runs/${encodeURIComponent(runId)}/evidence.json`;
    document.title = `${report.scenario?.name || "Mosaic"} — evidence`;
  }).catch(() => { id("run-title").textContent = "Evidence could not be loaded"; id("run-situation").textContent = "Return to the evidence history and choose another run."; });
})();
