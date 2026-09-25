/**
 * App wiring: connects the voice client, medicine search, prescription
 * table, manual-entry modal, and print/save/PDF flow together.
 */

(function () {
  "use strict";

  const RESULTS_PAGE_SIZE = 5;

  // ---------------------------------------------------------------- DOM refs
  const micButton = document.getElementById("micButton");
  const voiceHint = document.getElementById("voiceHint");
  const recognizedText = document.getElementById("recognizedText");
  const voiceError = document.getElementById("voiceError");
  const liveBadge = document.getElementById("liveBadge");
  const detectLine = document.getElementById("detectLine");
  const detectText = document.getElementById("detectText");
  const searchingLine = document.getElementById("searchingLine");
  const addRecognizedBtn = document.getElementById("addRecognizedBtn");

  const searchForm = document.getElementById("searchForm");
  const searchInput = document.getElementById("searchInput");
  const resultsBody = document.getElementById("resultsBody");
  const resultsFor = document.getElementById("resultsFor");
  const resultsForTerm = document.getElementById("resultsForTerm");
  const resultsFooter = document.getElementById("resultsFooter");
  const resultsCount = document.getElementById("resultsCount");
  const viewMoreBtn = document.getElementById("viewMoreBtn");

  const addManualBtn = document.getElementById("addManualBtn");
  const clearAllBtn = document.getElementById("clearAllBtn");
  const modalBackdrop = document.getElementById("modalBackdrop");
  const modalTitle = document.getElementById("modalTitle");
  const modalClose = document.getElementById("modalClose");
  const modalCancel = document.getElementById("modalCancel");
  const modalSubmit = document.getElementById("modalSubmit");
  const medicineForm = document.getElementById("medicineForm");

  const formItemId = document.getElementById("formItemId");
  const formMedicineName = document.getElementById("formMedicineName");
  const formStrength = document.getElementById("formStrength");
  const formFrequency = document.getElementById("formFrequency");
  const formDuration = document.getElementById("formDuration");
  const formInstructions = document.getElementById("formInstructions");

  const prescriptionBody = document.getElementById("prescriptionBody");

  const backendIconBadge = document.getElementById("backendIconBadge");
  const backendTitle = document.getElementById("backendTitle");
  const backendSub = document.getElementById("backendSub");
  const dbStatus = document.getElementById("dbStatus");
  const apiStatus = document.getElementById("apiStatus");
  const responseTime = document.getElementById("responseTime");

  const saveBtn = document.getElementById("saveBtn");
  const printBtn = document.getElementById("printBtn");
  const pdfBtn = document.getElementById("pdfBtn");

  const toastStack = document.getElementById("toastStack");

  const ICON_CHECK =
    '<svg viewBox="0 0 24 24" fill="none"><path d="M5 12.5 9.5 17 19 7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const ICON_WARN =
    '<svg viewBox="0 0 24 24" fill="none"><path d="M12 5 21 19.5H3L12 5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 10.5v4M12 17.5v.01" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/></svg>';
  const ICON_ERROR =
    '<svg viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"/></svg>';

  let lastVoiceText = "";
  let resultsFromVoice = false;
  let allResults = [];
  let visibleCount = RESULTS_PAGE_SIZE;

  // ---------------------------------------------------------------- voice detail parsing
  // Pulls Strength / Frequency / Duration / Instructions out of a spoken
  // sentence like "Amoxil 500 mg three times daily after meal for 5 days",
  // so selecting a voice match doesn't leave those fields blank.
  function parseVoiceDetails(text) {
    if (!text) return {};
    const lower = text.toLowerCase();
    const details = {};

    const strengthMatch = lower.match(/\b(\d+(?:[./]\d+)?)\s*(mg|mcg|ml|g|gm|iu)\b/);
    if (strengthMatch) {
      details.strength = `${strengthMatch[1]}${strengthMatch[2]}`;
    }

    const frequencyRules = [
      [/\b(once|one time)\s*(a\s*day|daily)?\b/, "Once daily"],
      [/\b(twice|two times)\s*(a\s*day|daily)?\b/, "Twice daily"],
      [/\b(thrice|three times)\s*(a\s*day|daily)?\b/, "Thrice daily"],
      [/\bfour times\s*(a\s*day|daily)?\b/, "Four times daily"],
    ];
    for (const [pattern, value] of frequencyRules) {
      if (pattern.test(lower)) {
        details.frequency = value;
        break;
      }
    }
    if (!details.frequency) {
      const everyXHours = lower.match(/\bevery\s*(\d+)\s*hours?\b/);
      if (everyXHours) details.frequency = `Every ${everyXHours[1]} hours`;
    }

    const durationMatch = lower.match(/\b(\d+)\s*(day|days|week|weeks|month|months)\b/);
    if (durationMatch) {
      const unit = durationMatch[2].startsWith("day")
        ? "day"
        : durationMatch[2].startsWith("week")
        ? "week"
        : "month";
      const n = parseInt(durationMatch[1], 10);
      details.duration = `${n} ${unit}${n === 1 ? "" : "s"}`;
    }

    if (/\bafter\s*(meal|meals|food|eating)\b/.test(lower)) {
      details.instructions = "After food";
    } else if (/\bbefore\s*(meal|meals|food|eating)\b|\bempty stomach\b/.test(lower)) {
      details.instructions = "Before food";
    } else if (/\bbedtime|before sleep|at night\b/.test(lower)) {
      details.instructions = "At bedtime";
    } else if (/\bwith water\b/.test(lower)) {
      details.instructions = "With water";
    }

    return details;
  }

  // ---------------------------------------------------------------- add a chosen result
  // Adds a medicine the doctor has explicitly picked (from the search
  // results table) to the prescription. Nothing is ever auto-added without
  // the doctor selecting it first.
  async function addResultToPrescription(result, voiceDetails, source) {
    await PrescriptionStore.add({
      medicine_name: result.medicine_name,
      strength: result.strength || voiceDetails.strength || null,
      frequency: voiceDetails.frequency || null,
      duration: voiceDetails.duration || null,
      instructions: voiceDetails.instructions || null,
      source,
      match_score: result.match_score,
    });
  }

  // ---------------------------------------------------------------- toasts
  function toast(message, type = "info") {
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    toastStack.appendChild(el);
    setTimeout(() => el.remove(), 3500);
  }

  // ---------------------------------------------------------------- health check
  async function checkHealth() {
    const started = performance.now();
    try {
      const res = await fetch("/api/health");
      const elapsed = Math.round(performance.now() - started);
      const data = await res.json();

      responseTime.textContent = `${elapsed} ms`;

      const problems = [];
      if (!data.medicine_catalog_loaded) problems.push("medicine.csv is missing");
      if (!data.whisper_ready) problems.push("voice model is not ready");

      if (problems.length === 0) {
        backendIconBadge.className = "status-icon-badge";
        backendIconBadge.innerHTML = ICON_CHECK;
        backendTitle.textContent = "Backend is Working";
        backendSub.textContent = "Connected to server successfully";
        backendSub.className = "status-sub";
      } else {
        backendIconBadge.className = "status-icon-badge warn";
        backendIconBadge.innerHTML = ICON_WARN;
        backendTitle.textContent = "Backend has warnings";
        backendSub.textContent = problems.join(" · ");
        backendSub.className = "status-sub warn";
      }

      dbStatus.textContent = data.medicine_catalog_loaded
        ? `Connected (${data.medicine_count.toLocaleString()} items)`
        : "Not connected";
      dbStatus.className = "status-sub" + (data.medicine_catalog_loaded ? "" : " error");

      apiStatus.textContent = "Online";
      apiStatus.className = "status-sub";
    } catch {
      responseTime.textContent = "\u2014";
      backendIconBadge.className = "status-icon-badge error";
      backendIconBadge.innerHTML = ICON_ERROR;
      backendTitle.textContent = "Backend unreachable";
      backendSub.textContent = "Could not connect to the server";
      backendSub.className = "status-sub error";
      dbStatus.textContent = "Unknown";
      dbStatus.className = "status-sub error";
      apiStatus.textContent = "Offline";
      apiStatus.className = "status-sub error";
    }
  }
  checkHealth();
  setInterval(checkHealth, 30000);

  // ---------------------------------------------------------------- voice
  const voice = new VoiceClient({
    onStatus: (message) => {
      voiceError.hidden = true;
      if (message === "listening") {
        setMicState("recording");
        voiceHint.textContent = "Listening… tap again to stop";
        liveBadge.hidden = false;
      } else if (message === "processing voice...") {
        setMicState("processing");
        voiceHint.textContent = "Processing… converting speech to text";
      }
    },
    onResult: (text) => {
      setMicState("idle");
      voiceHint.textContent = "Click the microphone to start voice input";
      liveBadge.hidden = true;
      recognizedText.value = text;
      lastVoiceText = text;
      resultsFromVoice = true;
      addRecognizedBtn.disabled = !text.trim();

      detectText.textContent = "Review/edit the text, then click \u201cSearch Medicine\u201d.";
      detectLine.hidden = false;
    },
    onError: (message) => {
      setMicState("idle");
      voiceHint.textContent = "Click the microphone to start voice input";
      liveBadge.hidden = true;
      voiceError.textContent = message;
      voiceError.hidden = false;
    },
  });

  function setMicState(state) {
    micButton.classList.remove("recording", "processing");
    if (state === "recording") {
      micButton.classList.add("recording");
      micButton.setAttribute("aria-pressed", "true");
    } else if (state === "processing") {
      micButton.classList.add("processing");
      micButton.setAttribute("aria-pressed", "false");
    } else {
      micButton.setAttribute("aria-pressed", "false");
    }
  }

  micButton.addEventListener("click", async () => {
    if (micButton.classList.contains("processing")) return;

    if (micButton.classList.contains("recording")) {
      voice.stop();
      return;
    }

    try {
      voiceError.hidden = true;
      detectLine.hidden = true;
      await voice.start();
    } catch {
      setMicState("idle");
    }
  });

  recognizedText.addEventListener("input", () => {
    addRecognizedBtn.disabled = !recognizedText.value.trim();
  });

  addRecognizedBtn.addEventListener("click", async () => {
    const text = recognizedText.value;
    if (!text || !text.trim()) {
      toast("Nothing to search \u2014 the recognized text is empty.", "error");
      return;
    }
    resultsFromVoice = true;
    lastVoiceText = text;
    detectLine.hidden = true;
    searchInput.value = text;
    await runSearch(text);
    resultsFor.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  // ---------------------------------------------------------------- search
  async function runSearch(query) {
    if (!query || !query.trim()) return null;

    searchingLine.hidden = false;
    resultsFor.hidden = true;
    resultsFooter.hidden = true;
    resultsBody.innerHTML = `<tr class="empty-row"><td colspan="6">Searching&hellip;</td></tr>`;

    try {
      const res = await fetch(`/api/medicines/search?q=${encodeURIComponent(query)}&max_results=50`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Search failed.");
      }
      const data = await res.json();
      allResults = data.results || [];
      visibleCount = RESULTS_PAGE_SIZE;

      resultsForTerm.textContent = query;
      resultsFor.hidden = false;

      renderResults(data.message);
      return data;
    } catch (err) {
      resultsBody.innerHTML = `<tr class="empty-row"><td colspan="6">${escapeHtml(err.message)}</td></tr>`;
      return null;
    } finally {
      searchingLine.hidden = true;
    }
  }

  function renderResults(message) {
    if (!allResults.length) {
      resultsBody.innerHTML = `<tr class="empty-row"><td colspan="6">${escapeHtml(
        message || "No matching medicine found."
      )}</td></tr>`;
      resultsFooter.hidden = true;
      return;
    }

    const shown = allResults.slice(0, visibleCount);
    const bestScore = allResults[0].match_score;

    resultsBody.innerHTML = "";
    shown.forEach((r, i) => {
      const tr = document.createElement("tr");
      const score = Math.round(r.match_score);
      const scoreClass = score >= 90 ? "match-high" : score >= 70 ? "match-mid" : "match-low";
      const isBest = i === 0 && r.match_score === bestScore;
      tr.innerHTML = `
        <td class="col-idx">${i + 1}</td>
        <td class="medicine-name-cell">${escapeHtml(r.medicine_name)}</td>
        <td>${escapeHtml(r.strength || "\u2014")}</td>
        <td>${escapeHtml(r.form || "\u2014")}</td>
        <td>
          <span class="match-score ${scoreClass}">${score}%</span>
          ${isBest ? `<span class="best-match-tag">Best Match</span>` : ""}
        </td>
        <td class="col-action">
          <button class="btn-select" data-index="${i}">+ Add</button>
        </td>
      `;
      resultsBody.appendChild(tr);
    });

    resultsFooter.hidden = false;
    const from = 1;
    const to = shown.length;
    resultsCount.textContent = `Showing ${from} - ${to} of ${allResults.length} result${allResults.length === 1 ? "" : "s"}`;
    viewMoreBtn.hidden = visibleCount >= allResults.length;
  }

  viewMoreBtn.addEventListener("click", () => {
    visibleCount += RESULTS_PAGE_SIZE;
    renderResults();
  });

  resultsBody.addEventListener("click", async (e) => {
    const btn = e.target.closest(".btn-select");
    if (!btn) return;

    const result = allResults[Number(btn.dataset.index)];
    if (!result) return;

    try {
      const voiceDetails = resultsFromVoice ? parseVoiceDetails(lastVoiceText) : {};
      await addResultToPrescription(result, voiceDetails, resultsFromVoice ? "voice" : "manual");
      toast(`${result.medicine_name} added to prescription.`, "success");
    } catch (err) {
      toast(err.message, "error");
    }
  });

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    resultsFromVoice = false;
    detectLine.hidden = true;
    runSearch(searchInput.value);
  });

  // ---------------------------------------------------------------- manual add / edit modal
  function openModal(mode, item) {
    medicineForm.reset();
    if (mode === "edit" && item) {
      modalTitle.textContent = "Edit medicine";
      modalSubmit.textContent = "Save changes";
      formItemId.value = item.id;
      formMedicineName.value = item.medicine_name || "";
      formStrength.value = item.strength || "";
      formFrequency.value = item.frequency || "";
      formDuration.value = item.duration || "";
      formInstructions.value = item.instructions || "";
    } else {
      modalTitle.textContent = "Add medicine manually";
      modalSubmit.textContent = "Add to prescription";
      formItemId.value = "";
    }
    modalBackdrop.hidden = false;
    formMedicineName.focus();
  }

  function closeModal() {
    modalBackdrop.hidden = true;
  }

  addManualBtn.addEventListener("click", () => openModal("add"));
  modalClose.addEventListener("click", closeModal);
  modalCancel.addEventListener("click", closeModal);
  modalBackdrop.addEventListener("click", (e) => {
    if (e.target === modalBackdrop) closeModal();
  });

  medicineForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      medicine_name: formMedicineName.value.trim(),
      strength: formStrength.value.trim() || null,
      frequency: formFrequency.value.trim() || null,
      duration: formDuration.value.trim() || null,
      instructions: formInstructions.value.trim() || null,
    };

    if (!payload.medicine_name) {
      toast("Medicine name is required.", "error");
      return;
    }

    try {
      if (formItemId.value) {
        await PrescriptionStore.update(formItemId.value, payload);
        toast("Medicine updated.", "success");
      } else {
        await PrescriptionStore.add({ ...payload, source: "manual" });
        toast("Medicine added to prescription.", "success");
      }
      closeModal();
    } catch (err) {
      toast(err.message, "error");
    }
  });

  // ---------------------------------------------------------------- prescription table actions
  prescriptionBody.addEventListener("click", async (e) => {
    const row = e.target.closest("tr[data-id]");
    if (!row) return;
    const id = row.dataset.id;

    if (e.target.closest(".edit-btn")) {
      const item = PrescriptionStore.find(id);
      if (item) openModal("edit", item);
    } else if (e.target.closest(".delete-btn")) {
      try {
        await PrescriptionStore.remove(id);
        toast("Medicine removed.", "success");
      } catch (err) {
        toast(err.message, "error");
      }
    }
  });

  prescriptionBody.addEventListener("change", async (e) => {
    const select = e.target.closest(".freq-select");
    if (!select) return;
    try {
      await PrescriptionStore.update(select.dataset.id, { frequency: select.value });
    } catch (err) {
      toast(err.message, "error");
    }
  });

  clearAllBtn.addEventListener("click", async () => {
    if (!PrescriptionStore.items.length) return;
    if (!confirm("Remove all medicines from the current prescription?")) return;
    try {
      await PrescriptionStore.clearAll();
      toast("Prescription cleared.", "success");
    } catch (err) {
      toast(err.message, "error");
    }
  });

  // ---------------------------------------------------------------- save / print / pdf / new
  saveBtn.addEventListener("click", async () => {
    if (!window.currentPatientId) {
      toast("Select a patient before saving a prescription.", "error");
      return;
    }
    try {
      await PrescriptionStore.confirm();

      // Doctor has reviewed and confirmed the draft — persist it to the
      // patient's permanent record (Module 3: Confirm -> Save to Patient Record).
      const summary = PrescriptionStore.items
        .map((i) => [i.medicine_name, i.strength, i.frequency, i.duration].filter(Boolean).join(" "))
        .join("; ");
      await apiFetch("/api/prescriptions", {
        method: "POST",
        body: JSON.stringify({
          patient_id: window.currentPatientId,
          prescription_text: summary,
          items: PrescriptionStore.items.map((i) => ({
            medicine_name: i.medicine_name,
            strength: i.strength,
            frequency: i.frequency,
            duration: i.duration,
            instructions: i.instructions,
            source: i.source,
          })),
          source: "voice",
        }),
      });

      toast("Prescription saved to patient record.", "success");
    } catch (err) {
      toast(err.message, "error");
    }
  });

  printBtn.addEventListener("click", () => {
    if (!PrescriptionStore.items.length) {
      toast("Add at least one medicine before printing.", "error");
      return;
    }
    document.getElementById("printDate").textContent = new Date().toLocaleDateString();
    window.print();
  });

  pdfBtn.addEventListener("click", () => {
    if (!PrescriptionStore.items.length) {
      toast("Add at least one medicine before downloading a PDF.", "error");
      return;
    }
    try {
      generatePdf(PrescriptionStore.items);
      toast("Prescription PDF downloaded.", "success");
    } catch (err) {
      console.error(err);
      toast("Could not generate the PDF.", "error");
    }
  });

  function generatePdf(items) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    doc.setFontSize(16);
    doc.setTextColor(11, 62, 145);
    doc.text("Voice Prescription", 14, 18);

    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(new Date().toLocaleString(), 14, 25);

    const headers = ["#", "Medicine", "Strength", "Frequency", "Duration", "Instructions"];
    const colWidths = [8, 46, 26, 32, 26, 44];
    let y = 38;

    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.setFillColor(11, 62, 145);
    let x = 14;
    headers.forEach((h, i) => {
      doc.rect(x, y - 5, colWidths[i], 8, "F");
      doc.text(h, x + 2, y);
      x += colWidths[i];
    });
    y += 8;

    doc.setTextColor(23, 34, 51);
    items.forEach((item, index) => {
      if (y > 275) {
        doc.addPage();
        y = 20;
      }
      const row = [
        String(index + 1),
        item.medicine_name || "-",
        item.strength || "-",
        item.frequency || "-",
        item.duration || "-",
        item.instructions || "-",
      ];
      x = 14;
      row.forEach((cell, i) => {
        const lines = doc.splitTextToSize(String(cell), colWidths[i] - 3);
        doc.text(lines, x + 2, y);
        x += colWidths[i];
      });
      y += 9;
      doc.setDrawColor(227, 232, 242);
      doc.line(14, y - 5.5, 196, y - 5.5);
    });

    doc.setFontSize(9);
    doc.setTextColor(120);
    doc.text("Doctor's signature: ____________________________", 14, y + 20);

    doc.save(`prescription-${new Date().toISOString().slice(0, 10)}.pdf`);
  }

  // ---------------------------------------------------------------- helpers
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
  }

  // ---------------------------------------------------------------- init
  PrescriptionStore.refresh().catch(() => toast("Could not load prescription.", "error"));
})();
