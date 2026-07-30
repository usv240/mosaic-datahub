(function () {
  "use strict";

  const id = (value) => document.getElementById(value);
  let csrf = "";

  try {
    const savedTheme = localStorage.getItem("mosaic-theme");
    if (savedTheme) document.documentElement.dataset.theme = savedTheme;
  } catch (error) {
    // Operating-system preference remains the fallback.
  }

  function currentTheme() {
    return document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  }

  function syncThemeButton() {
    id("theme-toggle").title = currentTheme() === "light" ? "Switch to dark theme" : "Switch to light theme";
  }

  id("theme-toggle").addEventListener("click", () => {
    const next = currentTheme() === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("mosaic-theme", next);
    } catch (error) {
      // Theme still applies for this page view.
    }
    syncThemeButton();
  });
  syncThemeButton();

  function escapeHTML(value) {
    return String(value).replace(/[&<>\"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
  }

  function cssState(value) {
    return String(value).replaceAll("_", "-");
  }

  fetch("/api/adoption")
    .then((response) => {
      if (!response.ok) throw new Error("Adoption contract unavailable");
      return response.json();
    })
    .then((catalog) => {
      id("adoption-status").textContent = "Live contract loaded · " + catalog.paths.length + " adoption stages";
      id("adoption-paths").innerHTML = catalog.paths
        .map((path) => '<article><span class="path-state ' + cssState(path.readiness) + '">' + escapeHTML(path.readiness.replaceAll("_", " ")) + "</span><small>" + escapeHTML(path.label) + "</small><h3>" + escapeHTML(path.setup) + "</h3><p>" + escapeHTML(path.action) + "</p><dl><div><dt>Proof at this stage</dt><dd>" + escapeHTML(path.proof) + "</dd></div></dl></article>")
        .join("");
      id("connector-matrix").innerHTML = catalog.connectors
        .map((connector) => '<article class="connector-row"><strong>' + escapeHTML(connector.label) + "</strong><p>" + escapeHTML(connector.detail) + '</p><span class="' + cssState(connector.status) + '">' + escapeHTML(connector.status.replaceAll("_", " ")) + "</span></article>")
        .join("");
      id("production-gates").innerHTML = catalog.production_gates
        .map((gate) => "<li>" + escapeHTML(gate) + "</li>")
        .join("");
      // Keep the exact API state visible for reviewers and contract tests.
      if (catalog.connectors.some((connector) => connector.status === "integration_required")) {
        id("connector-matrix").dataset.hasIntegrationBoundary = "true";
      }
    })
    .catch((error) => {
      id("adoption-status").textContent = error.message + ". See the repository deployment guide.";
    });

  function publishStatus(message) {
    id("publish-status").textContent = message;
  }

  fetch("/api/health/datahub")
    .then((response) => response.json())
    .then((data) => {
      id("server").textContent = data.server;
      id("connection").textContent = data.status.replaceAll("_", " ");
      if (!data.web_writeback_enabled) {
        publishStatus(data.public_demo ? "Read-only hosted demo: publication is disabled." : "Set MOSAIC_ENABLE_WEB_WRITEBACK=true locally to unlock approval.");
        return null;
      }
      return fetch("/api/approval-token")
        .then((response) => response.json())
        .then((token) => {
          csrf = token.csrf_token;
          id("publish").disabled = false;
          publishStatus("Approval gate ready. Exact confirmation is still required.");
        });
    })
    .catch(() => publishStatus("Could not load operator status."));

  id("probe").addEventListener("click", () => {
    id("connection").textContent = "Testing…";
    fetch("/api/health/datahub?probe=true")
      .then((response) => response.json())
      .then((data) => { id("connection").textContent = data.status; })
      .catch(() => { id("connection").textContent = "unavailable"; });
  });

  id("publish").addEventListener("click", () => {
    id("publish").disabled = true;
    publishStatus("Publishing and re-reading DataHub evidence…");
    fetch("/api/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csrf_token: csrf, confirmation: id("confirmation").value })
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Publication failed");
        publishStatus(data.status === "published" ? "Published. Every evidence type was re-read successfully." : "Result: " + data.status);
      })
      .catch((error) => {
        publishStatus(error.message);
        id("publish").disabled = false;
      });
  });
})();