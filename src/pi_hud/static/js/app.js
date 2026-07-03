// Minimal vanilla JS: fire clear actions, live-refresh the HUD preview.
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  e.preventDefault();
  btn.disabled = true;
  try {
    await fetch(btn.dataset.action, { method: "POST" });
    location.reload();
  } catch (err) {
    btn.disabled = false;
    alert("Request failed: " + err);
  }
});

// Refresh the physical-display preview so the dashboard stays live.
const hud = document.getElementById("hud");
if (hud) {
  setInterval(() => { hud.src = "/display.png?t=" + Date.now(); }, 3000);
}
