const typeFilter = document.getElementById("typeFilter");
const studentFilter = document.getElementById("studentFilter");
const loadBtn = document.getElementById("loadBtn");
const bodyEl = document.getElementById("recordsBody");

async function loadRecords() {
  bodyEl.innerHTML = "<tr><td colspan='7'>Loading...</td></tr>";
  const params = new URLSearchParams();
  if (typeFilter.value) params.set("answer_type", typeFilter.value);
  if (studentFilter.value.trim()) params.set("student_name", studentFilter.value.trim());
  params.set("limit", "500");

  const res = await fetch(`/api/submissions?${params.toString()}`);
  const data = await res.json();

  if (!res.ok) {
    bodyEl.innerHTML = `<tr><td colspan='7'>${data.detail || "Error"}</td></tr>`;
    return;
  }

  if (!data.length) {
    bodyEl.innerHTML = "<tr><td colspan='7'>No records</td></tr>";
    return;
  }

  bodyEl.innerHTML = data.map((r) => `
    <tr>
      <td>${r.id}</td>
      <td>${r.student_name}</td>
      <td>${r.rubric_id}</td>
      <td>${r.rubric_type}</td>
      <td>${r.total_score}/${r.max_total_score}</td>
      <td>${r.percentage}</td>
      <td>${r.created_at}</td>
    </tr>
  `).join("");
}

loadBtn.onclick = loadRecords;
loadRecords();
