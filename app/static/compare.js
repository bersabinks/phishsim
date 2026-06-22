"use strict";

const form = document.getElementById("compare-form");
if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("compare-msg");
    const fd = new FormData(e.target);
    const a = fd.get("campaign_a");
    const b = fd.get("campaign_b");

    try {
      const res = await fetch(`/api/compare?campaign_a=${a}&campaign_b=${b}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur " + res.status);
      renderComparison(data);
      document.getElementById("results-section").classList.remove("hidden");
      msg.textContent = "";
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "msg err";
    }
  });
}

function renderComparison(data) {
  const grid = document.getElementById("compare-grid");
  grid.innerHTML = "";

  ["campaign_a", "campaign_b"].forEach((key) => {
    const c = data[key];
    const col = document.createElement("div");
    col.className = "compare-col";

    const metrics = [
      ["Participants", c.participants_total],
      ["Ouvertures", c.ouvertures],
      ["Clics", c.clics],
      ["Signalements", c.signalements],
      ["Taux de clic", c.taux_clic + " %"],
      ["Taux de signalement", c.taux_signalement + " %"],
    ];

    const cards = metrics
      .map(
        ([label, value]) =>
          `<div class="metric">` +
          `<div class="value">${value}</div>` +
          `<div class="label">${escapeHtml(label)}</div>` +
          `</div>`
      )
      .join("");

    col.innerHTML =
      `<h3>${escapeHtml(c.name)} <span class="hint">(#${c.id})</span></h3>` +
      `<div class="results">${cards}</div>`;

    grid.appendChild(col);
  });
}

function escapeHtml(s) {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
