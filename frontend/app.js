document.addEventListener("DOMContentLoaded", () => {
  const slotsContainer = document.getElementById("uploadSlots");
  const addBtn = document.getElementById("addDocBtn");
  const compareBtn = document.getElementById("compareBtn");
  const loading = document.getElementById("loading");
  const results = document.getElementById("results");

  const LABELS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
  let slotIndex = 0;
  const fileMap = new Map();

  function createSlot() {
    if (slotIndex >= LABELS.length) return;
    const idx = slotIndex++;
    const label = LABELS[idx];
    const id = `file${label}`;
    const dropId = `drop${label}`;
    const nameId = `name${label}`;
    const boxId = `box${label}`;

    const box = document.createElement("div");
    box.className = "upload-box";
    box.id = boxId;

    box.innerHTML = `
      <div class="upload-box-header">
        <span class="upload-label">Documento ${label}</span>
        ${idx >= 2 ? `<button class="btn-remove" data-idx="${idx}" title="Quitar">✕</button>` : ""}
      </div>
      <input type="file" id="${id}" accept=".pdf" />
      <div class="drop-zone" id="${dropId}">
        <span class="drop-text">Arrastra o selecciona el PDF</span>
      </div>
      <span class="file-name" id="${nameId}"></span>
    `;

    slotsContainer.appendChild(box);

    const input = box.querySelector("input");
    const dropZone = box.querySelector(".drop-zone");
    const fileName = box.querySelector(`#${nameId}`);

    if (idx >= 2) {
      box.querySelector(".btn-remove").addEventListener("click", () => {
        fileMap.delete(idx);
        box.remove();
        checkReady();
      });
    }

    dropZone.addEventListener("click", () => input.click());

    input.addEventListener("change", () => {
      const file = input.files[0];
      if (file && file.type === "application/pdf") {
        fileMap.set(idx, file);
        fileName.textContent = file.name;
        dropZone.classList.add("has-file");
        dropZone.querySelector(".drop-text").textContent = file.name;
      }
      checkReady();
    });

    ["dragenter", "dragover"].forEach((ev) => {
      dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
      });
    });
    ["dragleave", "drop"].forEach((ev) => {
      dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
      });
    });
    dropZone.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files[0];
      if (file && file.type === "application/pdf") {
        fileMap.set(idx, file);
        fileName.textContent = file.name;
        dropZone.classList.add("has-file");
        dropZone.querySelector(".drop-text").textContent = file.name;
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
      }
      checkReady();
    });
  }

  function checkReady() {
    compareBtn.disabled = fileMap.size < 2;
  }

  addBtn.addEventListener("click", createSlot);

  createSlot();
  createSlot();

  compareBtn.addEventListener("click", async () => {
    loading.classList.remove("hidden");
    results.classList.add("hidden");

    const form = new FormData();
    for (const [idx, file] of fileMap) {
      form.append("files", file);
    }

    try {
      const resp = await fetch("/compare", { method: "POST", body: form });
      if (!resp.ok) {
        const err = await resp.json();
        alert("Error: " + (err.error || resp.statusText));
        return;
      }
      const data = await resp.json();
      renderResults(data);
    } catch (err) {
      alert("Error al comparar: " + err.message);
    } finally {
      loading.classList.add("hidden");
    }
  });
});

function renderResults(data) {
  const results = document.getElementById("results");
  results.classList.remove("hidden");
  renderSummary(data);
  renderItems(data.diff.items_comparison);
  renderIA(data.ia_analysis);
  setupTabs();
}

function renderSummary(data) {
  const bar = document.getElementById("summaryBar");
  const items = data.diff.items_comparison;
  const docs = data.documentos || [];

  let docInfo = docs
    .map((n, i) => `${chr(i)}: ${n} (${items.total_por_doc[i] || 0} items)`)
    .join(" &nbsp;|&nbsp; ");

  bar.innerHTML = `
    <strong>${items.cantidad_documentos} documentos comparados</strong>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <strong>Items en todos:</strong> ${items.en_todos}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <strong>Solo en un doc:</strong> ${items.solo_en_uno}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <strong>Códigos únicos:</strong> ${items.total_codigos_unicos}
    <br><small>${docInfo}</small>
  `;
}

let _exportData = null;

function chr(i) {
  return String.fromCharCode(65 + i);
}

function _normalize(s) {
  return (s || "").toLowerCase().replace(/\s+/g, " ").trim();
}

function downloadBlob(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function exportCSV() {
  if (!_exportData) return;
  const { itemsComp, n } = _exportData;
  const header = ["Código"];
  for (let i = 0; i < n; i++) header.push(`Nombre (${chr(i)})`);
  header.push("Presente en", "Estado");

  const rows = [header];
  for (const row of itemsComp.rows) {
    const presentes = [];
    for (let i = 0; i < n; i++) {
      if (row.presente[i]) presentes.push(chr(i));
    }
    let status = "";
    if (row.total_presente === n) {
      status = row.nombre_coincide_en_todos === false ? "Nombre difiere" : "En todos";
    } else if (row.total_presente === 0) {
      status = "En ninguno";
    } else {
      status = `Solo en ${presentes.join(", ")}`;
    }
    const line = [row.codigo];
    for (let i = 0; i < n; i++) line.push(row.nombres[i] || "");
    line.push(presentes.join(", ") || "—", status);
    rows.push(line);
  }

  const csv = rows
    .map((r) =>
      r
        .map((v) => {
          const s = String(v);
          return s.includes(",") || s.includes('"') || s.includes("\n")
            ? `"${s.replace(/"/g, '""')}"`
            : s;
        })
        .join(",")
    )
    .join("\n");

  downloadBlob("\uFEFF" + csv, "comparacion_items.csv", "text/csv;charset=utf-8");
}

function exportXLSX() {
  if (!_exportData) return;
  if (typeof XLSX === "undefined") {
    alert("La librería para Excel no está disponible. Usa la exportación CSV en su lugar.");
    return;
  }
  const { itemsComp, n } = _exportData;
  const header = ["Código"];
  for (let i = 0; i < n; i++) header.push(`Nombre (${chr(i)})`);
  header.push("Presente en", "Estado");

  const data = [header];
  for (const row of itemsComp.rows) {
    const presentes = [];
    for (let i = 0; i < n; i++) {
      if (row.presente[i]) presentes.push(chr(i));
    }
    let status = "";
    if (row.total_presente === n) {
      status = row.nombre_coincide_en_todos === false ? "Nombre difiere" : "En todos";
    } else if (row.total_presente === 0) {
      status = "En ninguno";
    } else {
      status = `Solo en ${presentes.join(", ")}`;
    }
    const line = [row.codigo];
    for (let i = 0; i < n; i++) line.push(row.nombres[i] || "");
    line.push(presentes.join(", ") || "—", status);
    data.push(line);
  }

  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(data);
  XLSX.utils.book_append_sheet(wb, ws, "Items");
  XLSX.writeFile(wb, "comparacion_items.xlsx");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("exportCsvBtn").addEventListener("click", exportCSV);
  document.getElementById("exportXlsxBtn").addEventListener("click", exportXLSX);
});

function renderItems(itemsComp) {
  const summary = document.getElementById("itemsSummary");
  const wrapper = document.getElementById("itemsTableWrapper");
  const exportBar = document.getElementById("exportBar");
  wrapper.innerHTML = "";
  summary.innerHTML = "";

  if (!itemsComp || !itemsComp.rows) {
    summary.innerHTML = "<p>No se pudieron extraer items de los documentos.</p>";
    return;
  }

  const n = itemsComp.cantidad_documentos;
  _exportData = { itemsComp, n };
  exportBar.style.display = "flex";
  const nameDiffs = itemsComp.rows.filter((r) => r.nombre_coincide_en_todos === false).length;

  summary.innerHTML = `
    <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1rem">
      <span><strong>Total items:</strong> ${itemsComp.total_por_doc.join(" / ")}</span>
      <span style="color:#2e7d32"><strong>✅ En todos:</strong> ${itemsComp.en_todos}</span>
      <span style="color:#c62828"><strong>❌ Solo en un doc:</strong> ${itemsComp.solo_en_uno}</span>
      <span style="color:#f57c00"><strong>⚡ Nombre difiere:</strong> ${nameDiffs}</span>
    </div>
  `;

  const table = document.createElement("table");
  table.className = "items-table";

  let headerHtml = "<tr><th>Código</th>";
  for (let i = 0; i < n; i++) {
    headerHtml += `<th>Nombre (${chr(i)})</th>`;
  }
  headerHtml += "<th>Presente en</th><th>Estado</th></tr>";
  table.innerHTML = `<thead>${headerHtml}</thead><tbody></tbody>`;
  wrapper.appendChild(table);

  const tbody = table.querySelector("tbody");

  const sorted = [...itemsComp.rows].sort((a, b) => {
    const score = (r) => {
      if (r.total_presente === 0) return 0;
      if (r.total_presente === 1) return 1;
      if (r.nombre_coincide_en_todos === false) return 2;
      return 3;
    };
    return score(a) - score(b);
  });

  for (const row of sorted) {
    const tr = document.createElement("tr");

    let presentes = [];
    let presentesStr = "";
    let status = "";
    let rowClass = "";

    for (let i = 0; i < n; i++) {
      if (row.presente[i]) {
        presentes.push(chr(i));
      }
    }
    presentesStr = presentes.join(", ") || "—";

    if (row.total_presente === n) {
      if (row.nombre_coincide_en_todos === false) {
        status = "⚠️ Nombre difiere";
        rowClass = "row-name-diff";
      } else {
        status = "✅ En todos";
        rowClass = "row-match";
      }
    } else if (row.total_presente === 0) {
      status = "❌ En ninguno";
      rowClass = "";
    } else {
      status = `⚠️ Solo en ${presentesStr}`;
      rowClass = "row-only-some";
    }

    let nombreCells = "";
    for (let i = 0; i < n; i++) {
      const name = row.nombres[i];
      const isDiff =
        row.total_presente === n &&
        row.nombre_coincide_en_todos === false &&
        name &&
        _normalize(name) !== _normalize(row.nombre_global);
      nombreCells += `<td class="${isDiff ? "cell-name-diff" : ""}">${
        name || "<em style='color:#999'>—</em>"
      }</td>`;
    }

    tr.className = rowClass;
    tr.innerHTML = `
      <td><strong>${row.codigo}</strong></td>
      ${nombreCells}
      <td>${presentesStr}</td>
      <td>${status}</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderIA(ia) {
  const container = document.getElementById("iaContainer");
  if (!ia || ia.resumen?.startsWith("No se pudo")) {
    container.innerHTML = `
      <div class="ia-section">
        <p style="color: #888;">${ia?.resumen || "Análisis IA no disponible. Verifica que Ollama esté corriendo."}</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="ia-section">
      <p style="font-size:1.1rem">${ia.resumen || ""}</p>
    </div>

    <div class="ia-section">
      <h4>Ítems que coinciden en todos</h4>
      <p style="font-size:1.5rem;font-weight:700;color:#2e7d32">${ia.items_en_todos ?? "N/A"}</p>
    </div>

    <div class="ia-section">
      <h4>Ítems faltantes</h4>
      ${ia.items_faltantes?.length
        ? `<ul>${ia.items_faltantes.map((d) => `<li>${d}</li>`).join("")}</ul>`
        : "<p style='color:#888'>No hay items faltantes.</p>"
      }
    </div>

    <div class="ia-section">
      <h4>Ítems con nombre diferente</h4>
      ${ia.items_nombre_diferente?.length
        ? `<ul>${ia.items_nombre_diferente.map((d) => `<li>${d}</li>`).join("")}</ul>`
        : "<p style='color:#888'>Todos los nombres coinciden.</p>"
      }
    </div>

    <div class="ia-section">
      <h4>Recomendación</h4>
      <p>${ia.recomendacion || "No hay recomendación disponible."}</p>
    </div>
  `;
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      const id = "tab" + btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1);
      document.getElementById(id).classList.add("active");
    });
  });
}
