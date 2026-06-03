document.addEventListener("DOMContentLoaded", () => {
  const fileA = document.getElementById("fileA");
  const fileB = document.getElementById("fileB");
  const dropZoneA = document.getElementById("dropZoneA");
  const dropZoneB = document.getElementById("dropZoneB");
  const fileNameA = document.getElementById("fileNameA");
  const fileNameB = document.getElementById("fileNameB");
  const compareBtn = document.getElementById("compareBtn");
  const loading = document.getElementById("loading");
  const results = document.getElementById("results");

  const files = { a: null, b: null };

  function setupDropZone(input, dropZone, fileNameEl, key) {
    dropZone.addEventListener("click", () => input.click());

    input.addEventListener("change", () => {
      const file = input.files[0];
      if (file && file.type === "application/pdf") {
        files[key] = file;
        fileNameEl.textContent = file.name;
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
        files[key] = file;
        fileNameEl.textContent = file.name;
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
    compareBtn.disabled = !(files.a && files.b);
  }

  setupDropZone(fileA, dropZoneA, fileNameA, "a");
  setupDropZone(fileB, dropZoneB, fileNameB, "b");

  compareBtn.addEventListener("click", async () => {
    loading.classList.remove("hidden");
    results.classList.add("hidden");

    const form = new FormData();
    form.append("file_a", files.a);
    form.append("file_b", files.b);

    try {
      const resp = await fetch("/compare", { method: "POST", body: form });
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
  renderDiff(data.diff.text_comparison);
  renderTables(data.diff.table_comparison);
  renderIA(data.ia_analysis);
  setupTabs();
}

function renderSummary(data) {
  const bar = document.getElementById("summaryBar");
  const diff = data.diff.text_comparison;
  const items = data.diff.items_comparison;
  const pct = diff.similarity_percentage;
  const pctClass = pct >= 95 ? "low" : pct >= 80 ? "medium" : "high";

  let itemsHtml = "";
  if (items) {
    const bothPct = items.total_a > 0 ? Math.round((items.en_ambos / Math.max(items.total_a, items.total_b)) * 100) : 0;
    const bothClass = bothPct >= 95 ? "low" : bothPct >= 80 ? "medium" : "high";
    itemsHtml = `&nbsp;&nbsp;|&nbsp;&nbsp;
      <strong>Items:</strong> ${items.en_ambos} coinciden
      <span class="ia-badge ${bothClass}" style="font-size:0.85rem">${bothPct}%</span>
      &nbsp;(${items.solo_a} solo A, ${items.solo_b} solo B)`;
  }

  bar.innerHTML = `
    <strong>Similitud general:</strong>
    <span class="ia-badge ${pctClass}">${pct}%</span>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <strong>Documento A:</strong> ${diff.total_lines_a} líneas
    &nbsp;&nbsp;
    <strong>Documento B:</strong> ${diff.total_lines_b} líneas
    ${itemsHtml}
  `;
}

function renderItems(itemsComp) {
  const summary = document.getElementById("itemsSummary");
  const wrapper = document.getElementById("itemsTableWrapper");
  wrapper.innerHTML = "";
  summary.innerHTML = "";

  if (!itemsComp || !itemsComp.rows) {
    summary.innerHTML = "<p>No se pudieron extraer items de los documentos.</p>";
    return;
  }

  const total = itemsComp.total_a + itemsComp.total_b;
  const eq = itemsComp.en_ambos - itemsComp.rows.filter(r => r.nombre_coincide === false).length;
  const nameDiff = itemsComp.rows.filter(r => r.nombre_coincide === false).length;

  summary.innerHTML = `
    <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1rem">
      <span><strong>Total items:</strong> ${itemsComp.total_a} (A) vs ${itemsComp.total_b} (B)</span>
      <span style="color:#2e7d32"><strong>✅ En ambos:</strong> ${itemsComp.en_ambos}</span>
      <span style="color:#c62828"><strong>❌ Solo A:</strong> ${itemsComp.solo_a}</span>
      <span style="color:#e65100"><strong>⚠️ Solo B:</strong> ${itemsComp.solo_b}</span>
      <span style="color:#f57c00"><strong>⚡ Nombre difiere:</strong> ${nameDiff}</span>
    </div>
  `;

  const table = document.createElement("table");
  table.className = "items-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Código</th>
        <th>Nombre en A</th>
        <th>Nombre en B</th>
        <th>Estado</th>
      </tr>
    </thead>
    <tbody id="itemsTbody"></tbody>
  `;
  wrapper.appendChild(table);

  const tbody = document.getElementById("itemsTbody");

  // Sort: solo A first, then solo B, then name diff, then match
  const sorted = [...itemsComp.rows].sort((a, b) => {
    const score = (r) => {
      if (r.en_a && !r.en_b) return 0;
      if (!r.en_a && r.en_b) return 1;
      if (r.nombre_coincide === false) return 2;
      return 3;
    };
    return score(a) - score(b);
  });

  for (const row of sorted) {
    const tr = document.createElement("tr");
    let status = "";
    let rowClass = "";

    if (row.en_a && row.en_b) {
      if (row.nombre_coincide === false) {
        status = "⚠️ Difiere nombre";
        rowClass = "row-name-diff";
      } else {
        status = "✅ Coincide";
        rowClass = "row-match";
      }
    } else if (row.en_a && !row.en_b) {
      status = "❌ Solo A";
      rowClass = "row-only-a";
    } else if (!row.en_a && row.en_b) {
      status = "⚠️ Solo B";
      rowClass = "row-only-b";
    }

    tr.className = rowClass;
    tr.innerHTML = `
      <td><strong>${row.codigo}</strong></td>
      <td>${row.nombre_a || "<em style='color:#999'>—</em>"}</td>
      <td>${row.nombre_b || "<em style='color:#999'>—</em>"}</td>
      <td>${status}</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderDiff(textComp) {
  const elA = document.getElementById("diffA");
  const elB = document.getElementById("diffB");
  elA.innerHTML = "";
  elB.innerHTML = "";

  for (const block of textComp.diff_blocks) {
    const tag = block.tag;
    const aLines = block.a_lines;
    const bLines = block.b_lines;

    if (tag === "equal") {
      aLines.forEach((l) => {
        const d = document.createElement("div");
        d.className = "line-equal";
        d.textContent = l;
        elA.appendChild(d);
      });
      bLines.forEach((l) => {
        const d = document.createElement("div");
        d.className = "line-equal";
        d.textContent = l;
        elB.appendChild(d);
      });
    } else if (tag === "replace") {
      aLines.forEach((l) => {
        const d = document.createElement("div");
        d.className = "line-replace";
        d.textContent = l;
        elA.appendChild(d);
      });
      bLines.forEach((l) => {
        const d = document.createElement("div");
        d.className = "line-replace";
        d.textContent = l;
        elB.appendChild(d);
      });
    } else if (tag === "delete") {
      aLines.forEach((l) => {
        const d = document.createElement("div");
        d.className = "line-delete";
        d.textContent = l;
        elA.appendChild(d);
      });
      bLines.forEach(() => {
        const d = document.createElement("div");
        d.className = "line-delete";
        d.textContent = "---";
        elB.appendChild(d);
      });
    } else if (tag === "insert") {
      aLines.forEach(() => {
        const d = document.createElement("div");
        d.className = "line-insert";
        d.textContent = "---";
        elA.appendChild(d);
      });
      bLines.forEach((l) => {
        const d = document.createElement("div");
        d.className = "line-insert";
        d.textContent = l;
        elB.appendChild(d);
      });
    }
  }
}

function renderTables(tablesComp) {
  const container = document.getElementById("tablesContainer");
  container.innerHTML = "";

  if (!tablesComp || tablesComp.length === 0) {
    container.innerHTML = "<p>No se detectaron tablas en los documentos.</p>";
    return;
  }

  for (const tbl of tablesComp) {
    const div = document.createElement("div");
    div.className = "table-diff";

    const status = tbl.match ? "✅ Coinciden" : "⚠️ Diferencias";
    div.innerHTML = `<h4>Tabla ${tbl.table_index + 1} — ${status} (A: ${tbl.rows_a} filas, B: ${tbl.rows_b} filas)</h4>`;

    if (tbl.match) {
      container.appendChild(div);
      continue;
    }

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    ["#", "Documento A", "Documento B", "¿Diferente?"].forEach((h) => {
      const th = document.createElement("th");
      th.textContent = h;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    const maxRows = Math.max(tbl.rows_a, tbl.rows_b);
    const diffRows = tbl.row_diffs || [];

    for (let i = 0; i < maxRows; i++) {
      const tr = document.createElement("tr");
      const tdIdx = document.createElement("td");
      tdIdx.textContent = i + 1;
      tr.appendChild(tdIdx);

      const tdA = document.createElement("td");
      const tdB = document.createElement("td");
      const tdDiff = document.createElement("td");

      const diffRow = diffRows.find((r) => r.row === i);
      if (diffRow) {
        tdA.textContent = (diffRow.a || []).join(" | ");
        tdA.className = "diff-cell";
        tdB.textContent = (diffRow.b || []).join(" | ");
        tdB.className = "diff-cell";
        tdDiff.textContent = "⚠️";
      } else {
        tdA.textContent = i < tbl.rows_a ? "✓" : "-";
        tdB.textContent = i < tbl.rows_b ? "✓" : "-";
        tdDiff.textContent = "—";
      }

      tr.appendChild(tdA);
      tr.appendChild(tdB);
      tr.appendChild(tdDiff);
      tbody.appendChild(tr);
    }

    table.appendChild(tbody);
    div.appendChild(table);
    container.appendChild(div);
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

  const coincidentes = ia.items_coincidentes ?? "N/A";

  container.innerHTML = `
    <div class="ia-section">
      <p style="font-size:1.1rem">${ia.resumen || ""}</p>
    </div>

    <div class="ia-section">
      <h4>Ítems que coinciden</h4>
      <p style="font-size:1.5rem;font-weight:700;color:#2e7d32">${coincidentes}</p>
    </div>

    <div class="ia-section">
      <h4>Ítems solo en Documento A</h4>
      ${ia.items_solo_en_a?.length
        ? `<ul>${ia.items_solo_en_a.map((d) => `<li>${d}</li>`).join("")}</ul>`
        : "<p style='color:#888'>No hay items exclusivos de A.</p>"
      }
    </div>

    <div class="ia-section">
      <h4>Ítems solo en Documento B</h4>
      ${ia.items_solo_en_b?.length
        ? `<ul>${ia.items_solo_en_b.map((d) => `<li>${d}</li>`).join("")}</ul>`
        : "<p style='color:#888'>No hay items exclusivos de B.</p>"
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
      document.getElementById("tab" + btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1)).classList.add("active");
    });
  });
}
