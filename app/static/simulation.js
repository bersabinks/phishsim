"use strict";

async function recordEvent(token, type, msgEl) {
  const fd = new FormData();
  fd.append("token", token);
  fd.append("event_type", type);
  try {
    const res = await fetch("/api/events", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Erreur");
    msgEl.textContent = data.duplicate
      ? "Déjà enregistré — merci."
      : "Merci, événement pédagogique enregistré (anonyme).";
    msgEl.className = "msg ok";
  } catch (err) {
    msgEl.textContent = err.message;
    msgEl.className = "msg err";
  }
}

const msgEl = document.getElementById("sim-msg");
["btn-clic", "btn-signalement"].forEach((id) => {
  const btn = document.getElementById(id);
  if (btn) {
    btn.addEventListener("click", () =>
      recordEvent(btn.dataset.token, btn.dataset.type, msgEl)
    );
  }
});
