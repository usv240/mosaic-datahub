const $ = (id) => document.getElementById(id);
const graph = $("graph");
const nodes = [
  ["zip", "ZIP5", "support_contacts.zip5", "Location enters from a support system."],
  ["dob", "Birth date", "support_contacts.full_birth_date", "A precise date creates highly specific groups when combined."],
  ["gender", "Gender", "member_demographics_coarse.gender_category", "A demographic attribute completes the three-family combination."],
  ["export", "Research export", "research_export_clean", "The lineage convergence is assessed here with an aggregate-only query."],
];
function drawGraph() { graph.innerHTML = nodes.map(([id,label,source,text]) => `<button class="node ${id === "export" ? "risk" : ""}" data-id="${id}" data-title="${label}" data-text="${text}"><span>${label}</span><small>${source}</small></button>`).join("") + '<div class="line l1"></div><div class="line l2"></div><div class="line l3"></div>'; graph.querySelectorAll(".node").forEach(n => n.addEventListener("click", () => { $("inspect-title").textContent = n.dataset.title; $("inspect-text").textContent = n.dataset.text; graph.querySelectorAll(".node").forEach(x => x.classList.toggle("selected", x === n)); })); }
function value(v, suffix="") { return v === undefined ? "â€”" : `${v}${suffix}`; }
async function load() { try { const r = await fetch("/api/assessment"); const data = await r.json(); const a = data.assessment; $("min-k").textContent = value(a.metrics.minimum_k); $("below-five").textContent = value(a.metrics.percent_below_5, "%"); $("raw-rows").textContent = value(a.raw_rows_returned); $("downstream").textContent = value(a.candidate.downstream_assets.length); const k = a.mitigation.metrics.minimum_k; $("after-k").textContent = `k=${k}`; $("after-k-card").textContent = `k=${k}`; } catch { document.querySelectorAll(".metric strong").forEach(el => el.textContent = "Offline"); } }
$("theme").addEventListener("click", () => { const root = document.documentElement; const light = root.dataset.theme !== "light"; root.dataset.theme = light ? "light" : "dark"; $("theme").textContent = light ? "â˜¾" : "â˜¼"; $("theme").setAttribute("aria-label", `Switch to ${light ? "dark" : "light"} mode`); localStorage.setItem("mosaic-theme", root.dataset.theme); });
document.documentElement.dataset.theme = localStorage.getItem("mosaic-theme") || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"); drawGraph(); load();
