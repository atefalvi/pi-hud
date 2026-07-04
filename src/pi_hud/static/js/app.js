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

// Copy-to-clipboard that also works on plain http (LAN), where
// navigator.clipboard is unavailable.
window.copyText = function (text, btn) {
  const done = () => {
    if (!btn) return;
    const old = btn.textContent;
    btn.textContent = "Copied";
    setTimeout(() => { btn.textContent = old; }, 1200);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done);
  } else {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
    done();
  }
};

document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-copy]");
  if (!btn) return;
  const el = document.querySelector(btn.dataset.copy);
  if (el) copyText(el.value !== undefined && el.tagName !== "CODE" ? el.value : el.textContent, btn);
});

// Refresh the physical-display preview so the dashboard stays live.
const hud = document.getElementById("hud");
if (hud) {
  setInterval(() => { hud.src = "/display.png?t=" + Date.now(); }, 3000);
}
