const rubricJson = document.getElementById("rubricJson");
const saveRubricBtn = document.getElementById("saveRubricBtn");
const rubricStatus = document.getElementById("rubricStatus");
const evaluateForm = document.getElementById("evaluateForm");
const resultBox = document.getElementById("resultBox");
const resultPanel = document.getElementById("resultPanel");
const rubricIdSelect = document.getElementById("rubricIdSelect");
const teacherActiveTypeText = document.getElementById("teacherActiveTypeText");
const studentActiveTypeText = document.getElementById("studentActiveTypeText");
const teacherRubricCards = document.getElementById("teacherRubricCards");

const teacherTypeButtons = Array.from(document.querySelectorAll("#teacherTypeTabs .tab-btn"));
const studentTypeButtons = Array.from(document.querySelectorAll("#studentTypeTabs .tab-btn"));

const teacherDashBtn = document.getElementById("teacherDashBtn");
const studentDashBtn = document.getElementById("studentDashBtn");
const teacherDashboard = document.getElementById("teacherDashboard");
const studentDashboard = document.getElementById("studentDashboard");

const defaults = {
  algorithm: {
    id: "algo-binary-search-v1",
    title: "Binary Search Algorithm Evaluation",
    question: "Write algorithm for Binary Search",
    answer_type: "algorithm",
    criteria: [
      { id: "logic", name: "Logic", description: "Core algorithm logic", max_score: 5, keywords: ["mid", "low", "high", "while"] },
      { id: "complexity", name: "Complexity", description: "Time complexity explained", max_score: 3, keywords: ["O(log n)", "sorted"] },
      { id: "clarity", name: "Clarity", description: "Clean structure", max_score: 2, keywords: ["if", "return"] }
    ]
  },
  flowchart: {
    id: "flow-binary-search-v1",
    title: "Binary Search Flowchart Evaluation",
    question: "Submit flowchart for Binary Search",
    answer_type: "flowchart",
    criteria: [
      { id: "symbols", name: "Flow Symbols", description: "Uses correct symbols", max_score: 4, keywords: ["start", "decision", "process", "end"] },
      { id: "logic", name: "Flow Logic", description: "Decision flow is correct", max_score: 4, keywords: ["mid", "low", "high", "true", "false"] },
      { id: "neatness", name: "Readability", description: "Readable and neat", max_score: 2, keywords: ["arrow", "label"] }
    ]
  },
  pseudocode: {
    id: "pseudo-binary-search-v1",
    title: "Binary Search Pseudocode Evaluation",
    question: "Write pseudocode for Binary Search",
    answer_type: "pseudocode",
    criteria: [
      { id: "syntax", name: "Pseudo Syntax", description: "Proper pseudocode style", max_score: 4, keywords: ["BEGIN", "END", "IF", "WHILE"] },
      { id: "steps", name: "Correct Steps", description: "Logical sequence", max_score: 4, keywords: ["mid", "low", "high", "return"] },
      { id: "quality", name: "Presentation", description: "Clarity and indentation", max_score: 2, keywords: ["indent", "step"] }
    ]
  }
};

let teacherType = "algorithm";
let studentType = "algorithm";

function switchDashboard(mode) {
  const teacherMode = mode === "teacher";
  teacherDashBtn.classList.toggle("active", teacherMode);
  studentDashBtn.classList.toggle("active", !teacherMode);
  teacherDashboard.classList.toggle("active-dashboard", teacherMode);
  studentDashboard.classList.toggle("active-dashboard", !teacherMode);
}

function setTeacherType(type) {
  teacherType = type;
  teacherActiveTypeText.textContent = type;
  teacherTypeButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.type === type));
  rubricJson.value = JSON.stringify(defaults[type], null, 2);
  loadTeacherRubricCards();
}

function setStudentType(type) {
  studentType = type;
  studentActiveTypeText.textContent = type;
  studentTypeButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.type === type));
  loadStudentRubricOptions();
}

async function fetchRubricsByType(type) {
  const res = await fetch(`/api/rubrics?answer_type=${encodeURIComponent(type)}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to load rubrics");
  return data;
}

async function loadTeacherRubricCards() {
  teacherRubricCards.innerHTML = "<div class='muted'>Loading cards...</div>";
  try {
    const rubrics = await fetchRubricsByType(teacherType);
    if (!rubrics.length) {
      teacherRubricCards.innerHTML = "<div class='muted'>No rubrics for this type.</div>";
      return;
    }

    teacherRubricCards.innerHTML = rubrics
      .map((r) => {
        const criteriaCount = Array.isArray(r.criteria) ? r.criteria.length : 0;
        return `
          <div class="rubric-card">
            <h4>${r.title}</h4>
            <div class="rubric-meta">ID: ${r.id} | Criteria: ${criteriaCount}</div>
            <div class="rubric-meta">Question: ${r.question}</div>
            <div class="card-actions">
              <button class="btn-edit" data-edit-id="${r.id}">Edit</button>
              <button class="btn-delete" data-delete-id="${r.id}">Delete</button>
            </div>
          </div>
        `;
      })
      .join("");

    teacherRubricCards.querySelectorAll("[data-edit-id]").forEach((btn) => {
      btn.addEventListener("click", () => editRubric(btn.dataset.editId));
    });

    teacherRubricCards.querySelectorAll("[data-delete-id]").forEach((btn) => {
      btn.addEventListener("click", () => deleteRubric(btn.dataset.deleteId));
    });
  } catch (err) {
    teacherRubricCards.innerHTML = `<div class='muted'>${String(err)}</div>`;
  }
}

async function loadStudentRubricOptions() {
  rubricIdSelect.innerHTML = "<option>Loading...</option>";
  try {
    const rubrics = await fetchRubricsByType(studentType);
    if (!rubrics.length) {
      rubricIdSelect.innerHTML = "<option value=''>No rubric for this type</option>";
      return;
    }

    rubricIdSelect.innerHTML = rubrics
      .map((r) => `<option value="${r.id}">${r.id} - ${r.title}</option>`)
      .join("");
  } catch (err) {
    rubricIdSelect.innerHTML = `<option value=''>${String(err)}</option>`;
  }
}

async function editRubric(rubricId) {
  try {
    const res = await fetch("/api/rubrics");
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to load rubric");
    const selected = data.find((r) => r.id === rubricId);
    if (!selected) throw new Error("Rubric not found");

    teacherType = selected.answer_type;
    teacherTypeButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.type === teacherType));
    teacherActiveTypeText.textContent = teacherType;
    rubricJson.value = JSON.stringify(selected, null, 2);
    switchDashboard("teacher");
    rubricStatus.textContent = `Editing rubric: ${rubricId}`;
  } catch (err) {
    rubricStatus.textContent = String(err);
  }
}

async function deleteRubric(rubricId) {
  const ok = window.confirm(`Delete rubric ${rubricId}?`);
  if (!ok) return;

  try {
    const res = await fetch(`/api/rubrics/${encodeURIComponent(rubricId)}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Delete failed");
    rubricStatus.textContent = `Deleted: ${rubricId}`;
    await loadTeacherRubricCards();
    await loadStudentRubricOptions();
  } catch (err) {
    rubricStatus.textContent = String(err);
  }
}

function buildTips(result) {
  const tips = [];
  (result.criterion_results || []).forEach((c) => {
    const ratio = c.max_score ? c.score / c.max_score : 0;
    if (ratio >= 0.75) return;

    const missing = c.reason && c.reason.includes(":") ? c.reason.split(":")[1].trim() : "main rubric points";
    tips.push(`Improve ${c.criterion_name}: include ${missing}.`);
    tips.push(`Rewrite ${c.criterion_name} in step-by-step format with clear keywords.`);
  });

  if (!tips.length) {
    tips.push("Great work. Keep same structure and add one dry-run example for full score consistency.");
  }

  return tips.slice(0, 4);
}

function renderResult(result) {
  const criteriaHtml = (result.criterion_results || []).map((c) => {
    const pct = c.max_score ? Math.round((c.score / c.max_score) * 100) : 0;
    return `
      <div class="criterion-row">
        <div class="criterion-head">
          <span>${c.criterion_name}</span>
          <span>${c.score}/${c.max_score}</span>
        </div>
        <div class="progress"><div style="width:${pct}%"></div></div>
        <div class="muted">${c.reason}</div>
      </div>
    `;
  }).join("");

  const tipsHtml = buildTips(result).map((t) => `<div class="tip-item">${t}</div>`).join("");

  const warningHtml = result.extraction_warning
    ? `<div class="tip-item">OCR Warning: ${result.extraction_warning}</div>`
    : "";

  resultPanel.classList.remove("muted");
  resultPanel.innerHTML = `
    <div class="result-top">
      <div class="score-card">
        <div class="score-percent">${Math.round(result.percentage)}%</div>
        <div>Score: ${result.total_score}/${result.max_total_score}</div>
        <div>Type: ${result.rubric_type}</div>
      </div>
      <div class="feedback-card">
        <h3>Feedback</h3>
        <div>${result.instant_feedback}</div>
      </div>
    </div>

    <div>
      <h3>Criterion Score Breakdown</h3>
      <div class="criteria-list">${criteriaHtml}</div>
    </div>

    <div>
      <h3>What To Improve Next</h3>
      <div class="tips-list">${tipsHtml}${warningHtml}</div>
    </div>
  `;
}

saveRubricBtn.addEventListener("click", async () => {
  rubricStatus.textContent = "Saving...";
  try {
    const payload = JSON.parse(rubricJson.value);
    payload.answer_type = teacherType;
    const res = await fetch("/api/rubrics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to save rubric");
    rubricStatus.textContent = `Saved: ${data.rubric_id} (${teacherType})`;
    await loadTeacherRubricCards();
    await loadStudentRubricOptions();
  } catch (err) {
    rubricStatus.textContent = String(err);
  }
});

evaluateForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const studentName = document.getElementById("studentName").value;
  const rubricId = rubricIdSelect.value;
  const file = document.getElementById("answerFile").files[0];

  if (!rubricId) {
    resultPanel.classList.add("muted");
    resultPanel.textContent = "Please select/create a rubric first.";
    return;
  }

  const form = new FormData();
  form.append("student_name", studentName);
  form.append("rubric_id", rubricId);
  form.append("answer_file", file);

  resultPanel.classList.add("muted");
  resultPanel.textContent = "Evaluating...";

  try {
    const res = await fetch("/api/evaluate", {
      method: "POST",
      body: form
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Evaluation failed");
    renderResult(data);
    resultBox.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    resultPanel.classList.add("muted");
    resultPanel.textContent = String(err);
    resultBox.textContent = String(err);
  }
});

teacherTypeButtons.forEach((btn) => {
  btn.addEventListener("click", () => setTeacherType(btn.dataset.type));
});

studentTypeButtons.forEach((btn) => {
  btn.addEventListener("click", () => setStudentType(btn.dataset.type));
});

teacherDashBtn.addEventListener("click", () => switchDashboard("teacher"));
studentDashBtn.addEventListener("click", () => switchDashboard("student"));

switchDashboard("teacher");
setTeacherType(teacherType);
setStudentType(studentType);
