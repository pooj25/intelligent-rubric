(() => {
  const STORAGE_KEY = "rubriq_theme";
  const root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    const btn = document.getElementById("global-theme-toggle");
    if (btn) {
      btn.textContent = theme === "dark" ? "Light" : "Dark";
      btn.setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} theme`);
    }
  }

  function ensureButton() {
    let btn = document.getElementById("global-theme-toggle");
    if (!btn) {
      btn = document.createElement("button");
      btn.id = "global-theme-toggle";
      btn.type = "button";
      btn.className = "floating-theme-toggle";
      document.body.appendChild(btn);
    }

    btn.addEventListener("click", () => {
      const current = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }

  const saved = localStorage.getItem(STORAGE_KEY);
  const initial = saved === "dark" || saved === "light"
    ? saved
    : (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

  ensureButton();
  applyTheme(initial);
})();
