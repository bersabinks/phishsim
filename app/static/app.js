"use strict";

let currentCampaignId = null;

function show(el, text, ok) {
  el.textContent = text;
  el.className = "msg " + (ok ? "ok" : "err");
}

async function postForm(url, formData) {
  const res = await fetch(url, { method: "POST", body: formData });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Erreur " + res.status);
  return data;
}

// --- Création de campagne ---
document.getElementById("campaign-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("campaign-msg");
  try {
    const data = await postForm("/api/campaigns", new FormData(e.target));
    show(msg, `Campagne #${data.id} créée (statut ${data.status}).`, true);
    setTimeout(() => location.reload(), 700);
  } catch (err) {
    show(msg, err.message, false);
  }
});

// --- Sélection d'une campagne à gérer ---
document.querySelectorAll(".select-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    currentCampaignId = btn.dataset.id;
    document.getElementById("manage-name").textContent =
      btn.dataset.name + " (#" + currentCampaignId + ")";
    document.getElementById("manage-section").classList.remove("hidden");
    loadParticipants();
    document.getElementById("manage-section").scrollIntoView({ behavior: "smooth" });
  });
});

// --- Ajout participant ---
const pForm = document.getElementById("participant-form");
if (pForm) {
  pForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("participant-msg");
    if (!currentCampaignId) return show(msg, "Sélectionnez une campagne.", false);
    try {
      const data = await postForm(
        `/api/campaigns/${currentCampaignId}/participants`,
        new FormData(e.target)
      );
      show(msg, `Participant « ${data.alias} » ajouté.`, true);
      e.target.reset();
      loadParticipants();
    } catch (err) {
      show(msg, err.message, false);
    }
  });
}

// --- Import CSV ---
const iForm = document.getElementById("import-form");
if (iForm) {
  iForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("import-msg");
    if (!currentCampaignId) return show(msg, "Sélectionnez une campagne.", false);
    try {
      const data = await postForm(
        `/api/campaigns/${currentCampaignId}/participants/import`,
        new FormData(e.target)
      );
      let txt = `${data.imported_count} importé(s), ${data.error_count} erreur(s).`;
      if (data.errors && data.errors.length) txt += " " + data.errors.join(" | ");
      show(msg, txt, data.error_count === 0);
      loadParticipants();
    } catch (err) {
      show(msg, err.message, false);
    }
  });
}

// --- Liste des participants ---
async function loadParticipants() {
  if (!currentCampaignId) return;
  const res = await fetch(`/api/campaigns/${currentCampaignId}/participants`);
  const rows = await res.json();
  const tbody = document.querySelector("#participants-table tbody");
  tbody.innerHTML = "";
  rows.forEach((p) => {
    const tr = document.createElement("tr");
    const link = `${location.origin}/simulation/${p.token}`;
    tr.innerHTML =
      `<td>${escapeHtml(p.alias)}</td>` +
      `<td><a href="${link}" target="_blank">${p.token}</a></td>`;
    tbody.appendChild(tr);
  });
}

// --- Résultats agrégés ---
const refreshBtn = document.getElementById("refresh-results");
if (refreshBtn) {
  refreshBtn.addEventListener("click", async () => {
    if (!currentCampaignId) return;
    const res = await fetch(`/api/campaigns/${currentCampaignId}/results`);
    const r = await res.json();
    const container = document.getElementById("results");
    container.innerHTML = "";
    const metrics = [
      ["Participants", r.participants_total],
      ["Ouvertures", r.ouvertures],
      ["Clics", r.clics],
      ["Signalements", r.signalements],
      ["Taux de clic", r.taux_clic + " %"],
      ["Taux de signalement", r.taux_signalement + " %"],
    ];
    metrics.forEach(([label, value]) => {
      const div = document.createElement("div");
      div.className = "metric";
      div.innerHTML = `<div class="value">${value}</div><div class="label">${label}</div>`;
      container.appendChild(div);
    });
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
