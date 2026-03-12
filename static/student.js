const typeTabs = Array.from(document.querySelectorAll("#typeTabs button"));
const activeTypeEl = document.getElementById("activeType");
const rubricSelect = document.getElementById("rubricSelect");
const evalForm = document.getElementById("evalForm");
const resultPanel = document.getElementById("resultPanel");
const rawJson = document.getElementById("rawJson");

let activeType = "algorithm";

function buildTips(result) {
  const tips = [];
  (result.criterion_results || []).forEach((c) => {
    const ratio = c.max_score ? c.score / c.max_score : 0;
    if (ratio >= 0.75) return;
    const missing = c.reason && c.reason.includes(":") ? c.reason.split(":")[1].trim() : "rubric keywords";
    tips.push(`Improve ${c.criterion_name}: include ${missing}.`);
  });
  return tips.length ? tips : ["Good work. Add one example/dry-run for stronger answer."];
}

function renderResult(result) {
  const rows = (result.criterion_results || []).map((c) => {
    const pct = c.max_score ? Math.round((c.score / c.max_score) * 100) : 0;
    return `
      <div class="criterion-row">
        <b>${c.criterion_name}</b> (${c.score}/${c.max_score})
        <div class="progress"><div style="width:${pct}%"></div></div>
        <div class="small">${c.reason}</div>
      </div>
    `;
  }).join("");

  const tips = buildTips(result).map((x) => `<div class="tip">${x}</div>`).join("");
  const warn = result.extraction_warning ? `<div class="tip">OCR warning: ${result.extraction_warning}</div>` : "";

  resultPanel.innerHTML = `
    <div class="result-panel">
      <div class="result-top">
        <div class="score-card">
          <div class="pct">${Math.round(result.percentage)}%</div>
          <div>${result.total_score}/${result.max_total_score}</div>
          <div>${result.rubric_type}</div>
        </div>
        <div class="feedback-card">
          <b>Feedback</b>
          <div>${result.instant_feedback}</div>
        </div>
      </div>
      <div>${rows}</div>
      <div><b>What to improve</b>${tips}${warn}</div>
    </div>
  `;
}

async function loadRubrics() {
  rubricSelect.innerHTML = "<option>Loading...</option>";
  const res = await fetch(`/api/rubrics?answer_type=${encodeURIComponent(activeType)}`);
  const data = await res.json();
  if (!res.ok) {
    rubricSelect.innerHTML = `<option value=''>${data.detail || "error"}</option>`;
    return;
  }
  if (!data.length) {
    rubricSelect.innerHTML = "<option value=''>No rubrics found. Ask teacher to create one.</option>";
    return;
  }
  rubricSelect.innerHTML = data.map((r) => `<option value="${r.id}">${r.id} - ${r.title}</option>`).join("");
}

function setType(type) {
  activeType = type;
  activeTypeEl.textContent = type;
  typeTabs.forEach((b) => b.classList.toggle("active", b.dataset.type === type));
  loadRubrics();
}

evalForm.onsubmit = async (e) => {
  e.preventDefault();
  const studentName = document.getElementById("studentName").value;
  const rubricId = rubricSelect.value;
  const file = document.getElementById("answerFile").files[0];

  if (!rubricId) {
    resultPanel.textContent = "Rubric select pannunga.";
    return;
  }

  const form = new FormData();
  form.append("student_name", studentName);
  form.append("rubric_id", rubricId);
  form.append("answer_file", file);

  resultPanel.textContent = "Evaluating...";

  const res = await fetch("/api/evaluate", { method: "POST", body: form });
  const data = await res.json();
  if (!res.ok) {
    resultPanel.textContent = data.detail || "Evaluation failed";
    rawJson.textContent = JSON.stringify(data, null, 2);
    return;
  }

  renderResult(data);
  rawJson.textContent = JSON.stringify(data, null, 2);
};

typeTabs.forEach((b) => (b.onclick = () => setType(b.dataset.type)));
setType(activeType);
