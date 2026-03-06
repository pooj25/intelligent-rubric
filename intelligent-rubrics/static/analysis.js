const statsEl = document.getElementById("stats");
const typeChart = document.getElementById("typeChart");
const weakChart = document.getElementById("weakChart");

function bar(label, value, max) {
  const width = max > 0 ? Math.round((value / max) * 100) : 0;
  return `
    <div class="criterion-row">
      <div><b>${label}</b> (${value})</div>
      <div class="progress"><div style="width:${width}%"></div></div>
    </div>
  `;
}

async function loadAnalysis() {
  const res = await fetch("/api/analysis");
  const data = await res.json();

  if (!res.ok) {
    statsEl.innerHTML = `<div class='stat'>${data.detail || "Error"}</div>`;
    return;
  }

  statsEl.innerHTML = `
    <div class="stat"><div>Total Submissions</div><div class="v">${data.total_submissions}</div></div>
    <div class="stat"><div>Average %</div><div class="v">${data.average_percentage}</div></div>
    <div class="stat"><div>Students</div><div class="v">${data.student_count}</div></div>
    <div class="stat"><div>Types Used</div><div class="v">${data.by_type.length}</div></div>
  `;

  const typeMax = Math.max(...(data.by_type || []).map((x) => x.count), 1);
  typeChart.innerHTML = (data.by_type || []).length
    ? data.by_type.map((x) => bar(`${x.type} (avg ${x.avg_percentage}%)`, x.count, typeMax)).join("")
    : "<div class='note'>No type data.</div>";

  const weakMax = Math.max(...(data.top_weak_criteria || []).map((x) => x.count), 1);
  weakChart.innerHTML = (data.top_weak_criteria || []).length
    ? data.top_weak_criteria.map((x) => bar(x.criterion, x.count, weakMax)).join("")
    : "<div class='note'>No weak criteria yet.</div>";
}

loadAnalysis();
