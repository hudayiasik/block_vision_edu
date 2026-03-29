/**
 * ui.js — tüm DOM işlemleri burada.
 * App mantığı hiçbir zaman DOM'a direkt dokunmaz.
 */

const UI = (() => {
  // Ekran referansları
  const screens = {
    menu:  document.getElementById('screen-menu'),
    stage: document.getElementById('screen-stage'),
    win:   document.getElementById('screen-win'),
  };

  function showScreen(name) {
    Object.entries(screens).forEach(([k, el]) => {
      if (el) el.style.display = k === name ? '' : 'none';
    });
  }

  // ── Menü ────────────────────────────────────────────────────────

  function renderStageSelect(stages, completedSet, onSelect) {
    const grid = document.getElementById('stage-grid');
    if (!grid) return;
    grid.innerHTML = '';
    stages.forEach((s, i) => {
      const locked = i > 0 && !completedSet.has(stages[i - 1].id);
      const done   = completedSet.has(s.id);
      const btn = document.createElement('button');
      btn.className = `stage-card ${locked ? 'locked' : ''} ${done ? 'done' : ''}`;
      btn.disabled = locked;
      btn.innerHTML = `
        <div class="sc-emoji">${done ? '✅' : locked ? '🔒' : s.emoji}</div>
        <div class="sc-num">Stage ${s.id}</div>
        <div class="sc-title">${s.title}</div>
      `;
      btn.addEventListener('click', () => {
        if (navigator.vibrate) navigator.vibrate(30);
        onSelect(s);
      });
      grid.appendChild(btn);
    });
  }

  // ── Stage ekranı ────────────────────────────────────────────────

  function setStageInfo(stageData) {
    const el = document.getElementById('stage-info');
    if (el) el.textContent = `Stage ${stageData.id} — ${stageData.title}`;
    const desc = document.getElementById('stage-desc');
    if (desc) desc.textContent = stageData.description;
    const hint = document.getElementById('stage-hint');
    if (hint) { hint.textContent = '💡 ' + stageData.hint; hint.style.display = 'none'; }
  }

  function showHint() {
    const hint = document.getElementById('stage-hint');
    if (hint) hint.style.display = '';
  }

  function setStatus(state, text) {
    const dot  = document.getElementById('status-dot');
    const txt  = document.getElementById('status-text');
    if (!dot || !txt) return;
    dot.className = `status-dot dot-${state}`;
    txt.textContent = text;
  }

  function renderProgramList(steps) {
    const list = document.getElementById('program-list');
    if (!list) return;
    list.innerHTML = '';
    if (!steps.length) {
      list.innerHTML = '<li class="prog-empty">Henüz program yok.</li>';
      return;
    }
    steps.forEach((s, i) => {
      const meta = CONFIG.BLOCK_META[s.action] || CONFIG.BLOCK_META.unknown;
      const li = document.createElement('li');
      li.className = 'prog-item';
      li.id = `prog-${i}`;
      li.innerHTML = `<span class="prog-num">${i+1}</span>
        <span class="prog-icon">${meta.icon}</span>
        <span class="prog-label">${meta.label}</span>`;
      list.appendChild(li);
    });
  }

  function highlightStep(idx) {
    document.querySelectorAll('.prog-item').forEach((el, i) => {
      el.classList.toggle('active', i === idx);
      if (i < idx) el.classList.add('done');
    });
    document.getElementById(`prog-${idx}`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function markAllDone() {
    document.querySelectorAll('.prog-item')
      .forEach(el => { el.classList.remove('active'); el.classList.add('done'); });
  }

  function renderChips(rawBlocks) {
    const box = document.getElementById('chips-box');
    const wrap = document.getElementById('chips-wrap');
    if (!box || !wrap) return;
    wrap.innerHTML = '';
    rawBlocks.forEach((name, i) => {
      const meta = CONFIG.BLOCK_META[name] || CONFIG.BLOCK_META.unknown;
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.style.background = meta.color + '22';
      chip.style.color = meta.color;
      chip.style.border = `1.5px solid ${meta.color}55`;
      chip.style.animationDelay = `${i * 50}ms`;
      chip.textContent = `${meta.icon} ${meta.label}`;
      wrap.appendChild(chip);
    });
    box.style.display = rawBlocks.length ? '' : 'none';
  }

  function setStepCounter(cur, total) {
    const el = document.getElementById('step-counter');
    if (el) el.textContent = `Adım ${cur} / ${total}`;
  }

  function setRunBtn(running) {
    const btn = document.getElementById('run-btn');
    if (!btn) return;
    btn.textContent = running ? '⏹ Durdur' : '▶ Çalıştır';
    btn.classList.toggle('running', running);
  }

  function setRunEnabled(enabled) {
    const btn = document.getElementById('run-btn');
    if (btn) btn.disabled = !enabled;
  }

  function showAnalyzing(show) {
    const overlay = document.getElementById('analyzing-overlay');
    if (overlay) overlay.style.display = show ? 'flex' : 'none';
  }

  // ── Kazanma ekranı ──────────────────────────────────────────────

  function showWin(stageData, stepCount) {
    showScreen('win');
    const title = document.getElementById('win-title');
    const sub   = document.getElementById('win-sub');
    if (title) title.textContent = `Stage ${stageData.id} Tamamlandı! 🎉`;
    if (sub)   sub.textContent   = `${stepCount} adımda başardın!`;
    _launchConfetti();
  }

  function _launchConfetti() {
    const canvas = document.getElementById('confetti-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    const pieces = Array.from({length: 80}, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * -canvas.height,
      w: 8 + Math.random() * 8,
      h: 6 + Math.random() * 6,
      color: ['#FF6B6B','#FFD93D','#6BCB77','#4D96FF','#FF6BFF'][Math.floor(Math.random()*5)],
      rot: Math.random() * 360,
      vx: (Math.random()-0.5)*3,
      vy: 2 + Math.random()*4,
      vr: (Math.random()-0.5)*6,
    }));
    let frame;
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pieces.forEach(p => {
        ctx.save();
        ctx.translate(p.x + p.w/2, p.y + p.h/2);
        ctx.rotate(p.rot * Math.PI/180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
        ctx.restore();
        p.x += p.vx; p.y += p.vy; p.rot += p.vr;
      });
      if (pieces.some(p => p.y < canvas.height)) {
        frame = requestAnimationFrame(draw);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    cancelAnimationFrame(frame);
    draw();
  }

  function showToast(msg, type = 'info', ms = 3000) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = `toast toast-${type} show`;
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), ms);
  }

  return {
    showScreen, renderStageSelect, setStageInfo, showHint,
    setStatus, renderProgramList, highlightStep, markAllDone,
    renderChips, setStepCounter, setRunBtn, setRunEnabled,
    showAnalyzing, showWin, showToast,
  };
})();
