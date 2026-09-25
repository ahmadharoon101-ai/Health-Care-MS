/**
 * PrescriptionStore — thin client around the /api/prescription REST endpoints,
 * plus rendering of the prescription table.
 */

const FREQUENCY_OPTIONS = [
  "Once daily",
  "Twice daily",
  "Thrice daily",
  "Four times daily",
  "Every 6 hours",
  "Every 8 hours",
  "As needed",
];

const EDIT_ICON =
  '<svg viewBox="0 0 24 24" fill="none"><path d="M14.5 5.5 18.5 9.5M4 20l.9-4 10.6-10.6a2 2 0 0 1 2.83 0l1.27 1.27a2 2 0 0 1 0 2.83L9 20l-4 0Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>';
const DELETE_ICON =
  '<svg viewBox="0 0 24 24" fill="none"><path d="M4 6.5h16M9 6.5V5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 5v1.5M6.5 6.5 7.3 19a2 2 0 0 0 2 1.9h5.4a2 2 0 0 0 2-1.9l.8-12.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>';

const PrescriptionStore = {
  items: [],
  confirmed: false,

  async refresh() {
    const res = await fetch("/api/prescription");
    if (!res.ok) throw new Error("Failed to load prescription.");
    this.items = await res.json();
    this.render();
  },

  async add(item) {
    const res = await fetch("/api/prescription", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to add medicine.");
    }
    this.confirmed = false;
    await this.refresh();
  },

  async update(id, updates) {
    const res = await fetch(`/api/prescription/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to update medicine.");
    }
    this.confirmed = false;
    await this.refresh();
  },

  async remove(id) {
    const res = await fetch(`/api/prescription/${id}`, { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to remove medicine.");
    }
    this.confirmed = false;
    await this.refresh();
  },

  async clearAll() {
    const res = await fetch("/api/prescription", { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to clear prescription.");
    }
    this.confirmed = false;
    await this.refresh();
  },

  async confirm() {
    const res = await fetch("/api/prescription/confirm", { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to confirm prescription.");
    }
    this.confirmed = true;
    this.render();
  },

  find(id) {
    return this.items.find((i) => i.id === id);
  },

  render() {
    const body = document.getElementById("prescriptionBody");
    const statusEl = document.getElementById("rxStatus");

    body.innerHTML = "";

    if (this.items.length === 0) {
      body.innerHTML = `<tr class="empty-row"><td colspan="7">No medicines added yet.</td></tr>`;
    } else {
      this.items.forEach((item, index) => {
        const tr = document.createElement("tr");
        tr.dataset.id = item.id;

        const freq = item.frequency || "";
        const isKnownFreq = FREQUENCY_OPTIONS.includes(freq);
        const options = FREQUENCY_OPTIONS.map(
          (opt) => `<option value="${escapeAttr(opt)}" ${opt === freq ? "selected" : ""}>${escapeHtml(opt)}</option>`
        ).join("");
        const customOption =
          freq && !isKnownFreq
            ? `<option value="${escapeAttr(freq)}" selected>${escapeHtml(freq)}</option>`
            : "";
        const blankOption = !freq ? `<option value="" selected disabled>Select&hellip;</option>` : "";

        tr.innerHTML = `
          <td class="col-idx">${index + 1}</td>
          <td class="medicine-name-cell">${escapeHtml(item.medicine_name)}${
            item.source === "voice" ? `<span class="source-tag">VOICE</span>` : ""
          }</td>
          <td>${escapeHtml(item.strength || "\u2014")}</td>
          <td>
            <select class="freq-select" data-id="${item.id}">
              ${blankOption}${customOption}${options}
            </select>
          </td>
          <td>${escapeHtml(item.duration || "\u2014")}</td>
          <td>${escapeHtml(item.instructions || "\u2014")}</td>
          <td class="col-action no-print">
            <button class="btn-icon edit-btn" title="Edit">${EDIT_ICON}</button>
            <button class="btn-icon danger delete-btn" title="Delete">${DELETE_ICON}</button>
          </td>
        `;
        body.appendChild(tr);
      });
    }

    const hasItems = this.items.length > 0;

    if (this.confirmed) {
      statusEl.textContent = "Prescription saved.";
      statusEl.classList.add("confirmed");
    } else {
      statusEl.textContent = hasItems ? "Not yet saved." : "Add at least one medicine to continue.";
      statusEl.classList.remove("confirmed");
    }
  },
};

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}
function escapeAttr(str) {
  return String(str).replace(/"/g, "&quot;");
}
