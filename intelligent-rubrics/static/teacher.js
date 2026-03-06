const typeTabs = Array.from(document.querySelectorAll("#typeTabs button"));
const activeTypeEl = document.getElementById("activeType");
const questionInput = document.getElementById("questionInput");
const rubricIdInput = document.getElementById("rubricIdInput");
const rubricJson = document.getElementById("rubricJson");
const generateBtn = document.getElementById("generateBtn");
const saveBtn = document.getElementById("saveBtn");
const statusEl = document.getElementById("status");
const cardsEl = document.getElementById("cards");

let activeType = "algorithm";

function setType(type) {
  activeType = type;
  activeTypeEl.textContent = type;
  typeTabs.forEach((b) => b.classList.toggle("active", b.dataset.type === type));
  loadCards();
}

async function loadCards() {
  cardsEl.innerHTML = "<div class='small'>Loading...</div>";
  try {
    const res = await fetch(`/api/rubrics?answer_type=${encodeURIComponent(activeType)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Load failed");

    if (!data.length) {
      cardsEl.innerHTML = "<div class='small'>No rubrics for this type.</div>";
      return;
    }

    cardsEl.innerHTML = data.map((r) => `
      <div class="rubric-card">
        <h4>${r.title}</h4>
        <div class="small">ID: ${r.id}</div>
        <div class="small">Q: ${r.question}</div>
        <div class="small">Criteria: ${r.criteria?.length || 0}</div>
        <div class="card-actions">
          <button class="secondary" data-edit="${r.id}">Edit</button>
          <button class="warn" data-del="${r.id}">Delete</button>
        </div>
      </div>
    `).join("");

    cardsEl.querySelectorAll("[data-edit]").forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.dataset.edit;
        const allRes = await fetch("/api/rubrics");
        const all = await allRes.json();
        const selected = all.find((x) => x.id === id);
        if (!selected) return;
        setType(selected.answer_type);
        rubricJson.value = JSON.stringify(selected, null, 2);
        statusEl.textContent = `Editing ${id}`;
      };
    });

    cardsEl.querySelectorAll("[data-del]").forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.dataset.del;
        if (!window.confirm(`Delete ${id}?`)) return;
        const res = await fetch(`/api/rubrics/${encodeURIComponent(id)}`, { method: "DELETE" });
        const data = await res.json();
        if (!res.ok) {
          statusEl.textContent = data.detail || "Delete failed";
          return;
        }
        statusEl.textContent = `Deleted ${id}`;
        loadCards();
      };
    });
  } catch (e) {
    cardsEl.innerHTML = `<div class='small'>${String(e)}</div>`;
  }
}

generateBtn.onclick = async () => {
  const question = questionInput.value.trim();
  if (!question) {
    statusEl.textContent = "Question enter pannunga";
    return;
  }

  statusEl.textContent = "Generating rubric...";
  const payload = {
    question,
    answer_type: activeType,
    rubric_id: rubricIdInput.value.trim() || null,
  };

  try {
    const res = await fetch("/api/rubrics/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Generation failed");
    rubricJson.value = JSON.stringify(data, null, 2);
    statusEl.textContent = "Generated. Review and save.";
  } catch (e) {
    statusEl.textContent = String(e);
  }
};

saveBtn.onclick = async () => {
  try {
    const payload = JSON.parse(rubricJson.value);
    payload.answer_type = activeType;
    const res = await fetch("/api/rubrics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Save failed");
    statusEl.textContent = `Saved ${data.rubric_id}`;
    loadCards();
  } catch (e) {
    statusEl.textContent = String(e);
  }
};

typeTabs.forEach((b) => (b.onclick = () => setType(b.dataset.type)));
setType(activeType);
