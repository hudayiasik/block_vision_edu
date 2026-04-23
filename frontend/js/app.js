/**
 * app.js — ana kontrolcü (Mediator).
 *
 * KRİTİK KURAL: Event listener'lar SADECE init() içinde bir kez bağlanır.
 * _onStageSelect veya başka fonksiyonlar listener EKLEMEZ — sadece _state değiştirir.
 * Bu sayede her "Run"da listener birikmez.
 */

const App = (() => {
  let _state = {
    currentStage: null,
    steps: [],
    stepCount: 0,
    isRunning: false,
    activeWs: null,
    completed: new Set(JSON.parse(localStorage.getItem('bv_completed') || '[]')),
  };

  // ── Init — listener'lar YALNIZCA burada, bir kez bağlanır ────────

  function init() {
    _bindAllEvents();
    UI.showScreen('menu');
    UI.renderStageSelect(CONFIG.STAGES, _state.completed, _onStageSelect);
  }

  function _bindAllEvents() {
    // Menü
    document.getElementById('btn-play').onclick = () => {
      if (navigator.vibrate) navigator.vibrate(30);
      document.getElementById('stage-select-section').style.display = '';
      document.getElementById('btn-play').style.display = 'none';
    };

    // Fotoğraf — onclick ile, tekrar bağlamaya gerek yok
    const fileInput = document.getElementById('file-input');
    const dropZone  = document.getElementById('drop-zone');

    fileInput.onchange = e => {
      const f = e.target.files[0];
      if (f) _onFileSelected(f);
      fileInput.value = '';
    };
    dropZone.onclick    = () => fileInput.click();
    dropZone.ondragover = e => { e.preventDefault(); dropZone.classList.add('drag-over'); };
    dropZone.ondragleave = () => dropZone.classList.remove('drag-over');
    dropZone.ondrop = e => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const f = e.dataTransfer.files[0];
      if (f) _onFileSelected(f);
    };

    // Stage kontrolleri
    document.getElementById('run-btn').onclick = () => {
      if (navigator.vibrate) navigator.vibrate(30);
      _state.isRunning ? _stopExecution() : _startExecution();
    };

    document.getElementById('reset-btn').onclick = () => {
      if (navigator.vibrate) navigator.vibrate(20);
      _onReset();
    };

    document.getElementById('hint-btn').onclick = () => UI.showHint();

    document.getElementById('back-btn').onclick = () => {
      if (_state.isRunning) _stopExecution();
      UI.showScreen('menu');
      UI.renderStageSelect(CONFIG.STAGES, _state.completed, _onStageSelect);
    };

    // Kazanma ekranı — onclick ile, her gösterimde üzerine yazılır
    document.getElementById('win-next-btn').onclick = _onWinNext;
    document.getElementById('win-retry-btn').onclick = _onWinRetry;
    document.getElementById('win-menu-btn').onclick  = _onWinMenu;
  }

  // ── Stage seçimi ─────────────────────────────────────────────────

  function _onStageSelect(stageData) {
    if (_state.isRunning) _stopExecution();

    _state.currentStage = stageData;
    _state.steps        = [];
    _state.stepCount    = 0;
    _state.isRunning    = false;
    _state.activeWs     = null;

    UI.showScreen('stage');
    UI.setStageInfo(stageData);
    UI.renderProgramList([]);
    UI.setRunEnabled(false);
    UI.setStatus('idle', 'Hazır');
    UI.renderChips([]);

    const stageEl = document.getElementById('stage');
    Stage.init(stageEl, stageData, {
      onWallHit:       _onWallHit,
      onTargetReached: _onTargetReached,
    });

    // Preview temizle
    const preview = document.getElementById('preview-img');
    if (preview) { preview.src = ''; preview.style.display = 'none'; }
  }

  // ── Dosya seçildi → otomatik analiz ──────────────────────────────

  async function _onFileSelected(file) {
    if (!_state.currentStage) return;
    if (!file.type.startsWith('image/')) {
      UI.showToast('Lutfen bir resim dosyasi sec!', 'error');
      return;
    }

    const preview = document.getElementById('preview-img');
    if (preview) {
      preview.src = URL.createObjectURL(file);
      preview.style.display = '';
    }

    UI.showAnalyzing(true);
    UI.setStatus('loading', 'Bloklar taranıyor...');
    UI.setRunEnabled(false);

    try {
      const result = await API.analyzeImage(file);

      if (!result.success || !result.steps?.length) {
        UI.showToast(result.error || 'Blok bulunamadi, tekrar dene!', 'error', 5000);
        UI.setStatus('error', 'Blok bulunamadı');
        return;
      }

      _state.steps = result.steps;
      UI.renderChips(result.raw_blocks);
      UI.renderProgramList(result.steps);
      UI.setRunEnabled(true);
      UI.setStatus('success', `${result.steps.length} adım hazır!`);
      UI.showToast(`${result.steps.length} blok bulundu! Calistir'a bas`, 'success');
      if (navigator.vibrate) navigator.vibrate([50, 30, 80]);

    } catch (err) {
      UI.showToast(`Hata: ${err.message}`, 'error', 6000);
      UI.setStatus('error', 'Analiz basarisiz');
    } finally {
      UI.showAnalyzing(false);
    }
  }

  // ── Çalıştırma ────────────────────────────────────────────────────

  function _startExecution() {
    if (!_state.steps.length || _state.isRunning) return;

    _state.isRunning  = true;
    _state.stepCount  = 0;
    UI.setRunBtn(true);
    UI.setStatus('running', 'Calisiyor...');
    Stage.reset();

    _state.activeWs = API.executeProgram(_state.steps, {
      onReset: () => {
        Stage.reset();
        UI.setStepCounter(0, _state.steps.length);
      },
      onStep: ({ stepIndex, action, totalSteps }) => {
        Stage.step(action);
        _state.stepCount = stepIndex + 1;
        UI.highlightStep(stepIndex);
        UI.setStepCounter(stepIndex + 1, totalSteps);
      },
      onDone: ({ totalSteps }) => {
        UI.markAllDone();
        UI.setStepCounter(totalSteps, totalSteps);
        _resetRunState();
        UI.setStatus('success', 'Bitti!');
      },
      onError: msg => {
        UI.showToast(`Baglanti hatasi: ${msg}`, 'error');
        _resetRunState();
        UI.setStatus('error', 'Hata');
      },
    });
  }

  function _stopExecution() {
    _state.activeWs?.close();
    _resetRunState();
    UI.setStatus('idle', 'Durduruldu');
  }

  function _resetRunState() {
    _state.isRunning = false;
    _state.activeWs  = null;
    UI.setRunBtn(false);
  }

  // ── Duvar / Hedef ─────────────────────────────────────────────────

  function _onWallHit() {
    UI.showToast('Duvara carpti!', 'error', 1500);
  }

  function _onTargetReached() {
    const stageData = _state.currentStage;
    _state.completed.add(stageData.id);
    localStorage.setItem('bv_completed', JSON.stringify([..._state.completed]));
    setTimeout(() => UI.showWin(stageData, _state.stepCount), 500);
  }

  // ── Kazanma ekranı butonları ──────────────────────────────────────

  function _onWinNext() {
    const stages = CONFIG.STAGES;
    const idx    = stages.findIndex(s => s.id === _state.currentStage.id);
    const next   = stages[idx + 1];
    if (next) {
      _onStageSelect(next);
    } else {
      UI.showScreen('menu');
      UI.renderStageSelect(CONFIG.STAGES, _state.completed, _onStageSelect);
      UI.showToast('Tum stageler tamamlandi!', 'success', 5000);
    }
  }

  function _onWinRetry() {
    _onStageSelect(_state.currentStage);
  }

  function _onWinMenu() {
    UI.showScreen('menu');
    UI.renderStageSelect(CONFIG.STAGES, _state.completed, _onStageSelect);
  }

  // ── Reset ─────────────────────────────────────────────────────────

  function _onReset() {
    if (_state.isRunning) _stopExecution();
    Stage.reset();
    _state.steps = [];
    UI.setRunEnabled(false);
    UI.renderProgramList([]);
    UI.renderChips([]);
    UI.setStatus('idle', 'Sifirlandı');
    const preview = document.getElementById('preview-img');
    if (preview) { preview.src = ''; preview.style.display = 'none'; }
  }

  function getSteps() { return _state.steps; }
  return { init, getSteps };
})();

document.addEventListener('DOMContentLoaded', () => App.init());

// Menü yıldızları
(function spawnStars() {
  const container = document.getElementById('menu-stars');
  if (!container) return;
  for (let i = 0; i < 40; i++) {
    const s = document.createElement('div');
    s.className = 'star-dot';
    const size = 1 + Math.random() * 3;
    s.style.cssText = `width:${size}px;height:${size}px;left:${Math.random()*100}%;top:${Math.random()*100}%;animation-duration:${3+Math.random()*6}s;animation-delay:${Math.random()*5}s;opacity:${0.3+Math.random()*0.7}`;
    container.appendChild(s);
  }
})();

// ══════════════════════════════════════════════════════════════
// BLUETOOTH MODÜLÜ — App.js ek bloğu
// ══════════════════════════════════════════════════════════════
const BtController = (() => {
  let _steps = [];  // app.js'den paylaşılacak

  function init(getStepsFn) {
    _getSteps = getStepsFn;

    // Durum değişimi callback
    Bluetooth.onStatusChange(status => {
      const dot   = document.getElementById('bt-dot');
      const label = document.getElementById('bt-connect-label');
      const txt   = document.getElementById('bt-status-text');
      const btn   = document.getElementById('bt-connect-btn');
      const hint  = document.getElementById('bt-hint');
      const runBtn = document.getElementById('bt-run-btn');

      dot.className = 'bt-dot ' + status;
      if (status === 'connected') {
        label.textContent = 'Bağlantıyı Kes';
        txt.textContent   = 'Robot bağlı ✓';
        btn.classList.add('connected');
        hint.classList.remove('show');
        runBtn.disabled = false;
        UI.showToast('Robot bağlandı! 🤖', 'success');
      } else {
        label.textContent = 'Robota Bağlan';
        txt.textContent   = 'Bağlı değil';
        btn.classList.remove('connected');
        runBtn.disabled = true;
      }
    });

    // Bağlan/Kes butonu
    document.getElementById('bt-connect-btn').onclick = async () => {
      if (navigator.vibrate) navigator.vibrate(30);
      if (Bluetooth.isConnected()) {
        await Bluetooth.disconnect();
      } else {
        const hint = document.getElementById('bt-hint');
        hint.classList.add('show');
        try {
          await Bluetooth.connect();
        } catch (err) {
          UI.showToast('Bağlantı hatası: ' + err.message, 'error', 6000);
          hint.classList.add('show');
        }
      }
    };

    // Robotu çalıştır
    document.getElementById('bt-run-btn').onclick = async () => {
      if (navigator.vibrate) navigator.vibrate(30);
      const steps = _getSteps();
      if (!steps.length) {
        UI.showToast('Önce blok fotoğrafı yükle!', 'error');
        return;
      }
      await _runRobot(steps);
    };
  }

  async function _runRobot(steps) {
    const log    = document.getElementById('bt-step-log');
    const runBtn = document.getElementById('bt-run-btn');
    runBtn.disabled = true;
    runBtn.textContent = '⏳ Çalışıyor...';

    const cmds = steps.map(s => Bluetooth.ACTION_TO_CMD[s.action]).filter(Boolean);
    log.textContent = `Gönderiliyor: ${cmds.join(' → ')}`;
    log.classList.add('active');

    try {
      await Bluetooth.executeSteps(steps, (idx, action) => {
        const cmd = Bluetooth.ACTION_TO_CMD[action] || '?';
        log.textContent = `Adım ${idx+1}/${steps.length}: [${cmd}] ${action}`;
        if (navigator.vibrate) navigator.vibrate(15);
      });
      log.textContent = '✓ Tamamlandı!';
      UI.showToast('Robot programı tamamladı! 🤖✅', 'success');
      if (navigator.vibrate) navigator.vibrate([50,30,100]);
    } catch (err) {
      log.textContent = 'Hata: ' + err.message;
      log.classList.remove('active');
      UI.showToast('Robot hatası: ' + err.message, 'error');
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = '🤖 Robotu Çalıştır';
    }
  }

  let _getSteps = () => [];
  function getSteps() { return _state.steps; }
  return { init, getSteps };
})();

// ── Bluetooth'u app başlatırken init et ───────────────────────
// (DOMContentLoaded zaten yukarıda var, bu append olduğu için çalışır)
document.addEventListener('DOMContentLoaded', () => {
  // _state.steps'e erişim için getter
  // Not: App modülünden steps'i okuyabilmek için küçük bridge
  if (typeof BtController !== 'undefined' && typeof Bluetooth !== 'undefined') {
    BtController.init(() => App.getSteps());
  }
});
