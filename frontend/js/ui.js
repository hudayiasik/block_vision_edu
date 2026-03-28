/**
 * ui.js — all DOM read/write operations.
 *
 * App logic never touches the DOM directly.
 * This keeps app.js clean and makes UI changes trivial.
 */

const UI = (() => {
  // ── Element references ────────────────────────────────────────────
  const els = {
    dropZone:      document.getElementById('drop-zone'),
    fileInput:     document.getElementById('file-input'),
    previewImg:    document.getElementById('preview-img'),
    analyzeBtn:    document.getElementById('analyze-btn'),
    runBtn:        document.getElementById('run-btn'),
    resetBtn:      document.getElementById('reset-btn'),
    statusDot:     document.querySelector('.dot'),
    statusText:    document.getElementById('status-text'),
    sequenceBox:   document.getElementById('sequence-box'),
    chipsContainer:document.getElementById('chips-container'),
    programList:   document.getElementById('program-list'),
    stepCounter:   document.getElementById('step-counter'),
    currentStep:   document.getElementById('current-step'),
    totalSteps:    document.getElementById('total-steps'),
    toast:         document.getElementById('toast'),
    colorGuideList:document.getElementById('color-guide-list'),
  };

  let _toastTimer = null;

  // ── Status bar ────────────────────────────────────────────────────

  const STATUS_CLASSES = ['dot--idle', 'dot--loading', 'dot--success', 'dot--running', 'dot--error'];

  function setStatus(state, text) {
    STATUS_CLASSES.forEach(c => els.statusDot.classList.remove(c));
    els.statusDot.classList.add(`dot--${state}`);
    els.statusText.textContent = text;
  }

  // ── Toast ─────────────────────────────────────────────────────────

  function showToast(message, type = 'info', durationMs = 3000) {
    clearTimeout(_toastTimer);
    els.toast.textContent = message;
    els.toast.className = `toast toast--${type} show`;
    _toastTimer = setTimeout(() => {
      els.toast.classList.remove('show');
    }, durationMs);
  }

  // ── Image preview ─────────────────────────────────────────────────

  function showImagePreview(file) {
    const url = URL.createObjectURL(file);
    els.previewImg.src = url;
    els.previewImg.hidden = false;
    els.dropZone.querySelector('.drop-zone__inner').style.display = 'none';
  }

  function clearImagePreview() {
    els.previewImg.hidden = true;
    els.previewImg.src = '';
    els.dropZone.querySelector('.drop-zone__inner').style.display = '';
  }

  // ── Sequence chips ────────────────────────────────────────────────

  function renderChips(rawBlocks) {
    els.chipsContainer.innerHTML = '';
    rawBlocks.forEach((blockName, i) => {
      const chip = document.createElement('span');
      const meta = CONFIG.BLOCK_META[blockName] || CONFIG.BLOCK_META.unknown;
      chip.className = `chip chip--${blockName}`;
      chip.textContent = `${meta.icon} ${meta.label}`;
      chip.style.animationDelay = `${i * 60}ms`;
      els.chipsContainer.appendChild(chip);
    });
    els.sequenceBox.hidden = false;
  }

  // ── Program list ──────────────────────────────────────────────────

  function renderProgramList(steps) {
    els.programList.innerHTML = '';
    if (!steps.length) {
      els.programList.innerHTML = '<li class="program-list__empty">No steps detected.</li>';
      return;
    }
    steps.forEach((step, i) => {
      const meta = CONFIG.BLOCK_META[step.action] || CONFIG.BLOCK_META.unknown;
      const li = document.createElement('li');
      li.className = 'program-item';
      li.id = `step-${i}`;
      li.innerHTML = `
        <span class="program-item__num">${i + 1}</span>
        <span class="program-item__icon">${meta.icon}</span>
        <span class="program-item__label">${meta.label}</span>
      `;
      li.style.animationDelay = `${i * 40}ms`;
      els.programList.appendChild(li);
    });
  }

  function highlightStep(index) {
    document.querySelectorAll('.program-item').forEach((el, i) => {
      el.classList.toggle('active', i === index);
      if (i < index) el.classList.add('done');
    });
    // Scroll active step into view
    const active = document.getElementById(`step-${index}`);
    active?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function markAllDone() {
    document.querySelectorAll('.program-item').forEach(el => {
      el.classList.remove('active');
      el.classList.add('done');
    });
  }

  // ── Step counter ──────────────────────────────────────────────────

  function showStepCounter(current, total) {
    els.stepCounter.hidden = false;
    els.currentStep.textContent = current;
    els.totalSteps.textContent = total;
  }

  function hideStepCounter() {
    els.stepCounter.hidden = true;
  }

  // ── Button states ─────────────────────────────────────────────────

  function setAnalyzeBtnEnabled(enabled) {
    els.analyzeBtn.disabled = !enabled;
  }

  function setRunBtnEnabled(enabled) {
    els.runBtn.disabled = !enabled;
  }

  function setRunBtnLabel(label) {
    els.runBtn.innerHTML = label;
  }

  // ── Color guide ───────────────────────────────────────────────────

  function renderColorGuide() {
    els.colorGuideList.innerHTML = '';
    CONFIG.COLOR_GUIDE.forEach(({ label, color }) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span class="swatch" style="background:${color}"></span>
        <span>${label}</span>
      `;
      els.colorGuideList.appendChild(li);
    });
  }

  // ── Expose ────────────────────────────────────────────────────────

  return {
    els,
    setStatus,
    showToast,
    showImagePreview,
    clearImagePreview,
    renderChips,
    renderProgramList,
    highlightStep,
    markAllDone,
    showStepCounter,
    hideStepCounter,
    setAnalyzeBtnEnabled,
    setRunBtnEnabled,
    setRunBtnLabel,
    renderColorGuide,
  };
})();
