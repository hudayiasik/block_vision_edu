/**
 * app.js — application controller.
 *
 * Wires UI events → API calls → Stage updates.
 * Contains zero DOM manipulation (delegated to UI module).
 * Contains zero movement logic (delegated to Stage module).
 *
 * Follows the Mediator pattern: app.js is the only place
 * that knows about all three modules.
 */

const App = (() => {
  // ── Application state ─────────────────────────────────────────────
  let _state = {
    selectedFile: null,   // File | null
    steps: [],            // StepSchema[]
    isRunning: false,
    activeWs: null,       // WebSocket | null
  };

  // ── Initialization ────────────────────────────────────────────────

  function init() {
    Stage.init();
    UI.renderColorGuide();
    _bindEvents();
    UI.setStatus('idle', 'Ready');
  }

  // ── Event binding ─────────────────────────────────────────────────

  function _bindEvents() {
    const { els } = UI;

    // Click on drop zone → open file picker
    els.dropZone.addEventListener('click', () => els.fileInput.click());
    els.dropZone.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') els.fileInput.click();
    });

    // Drag & drop
    els.dropZone.addEventListener('dragover', e => {
      e.preventDefault();
      els.dropZone.classList.add('drag-over');
    });
    els.dropZone.addEventListener('dragleave', () => {
      els.dropZone.classList.remove('drag-over');
    });
    els.dropZone.addEventListener('drop', e => {
      e.preventDefault();
      els.dropZone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) _onFileSelected(file);
    });

    // File input change (camera or gallery)
    els.fileInput.addEventListener('change', e => {
      const file = e.target.files[0];
      if (file) _onFileSelected(file);
    });

    // Analyze button
    els.analyzeBtn.addEventListener('click', _onAnalyze);

    // Run button
    els.runBtn.addEventListener('click', () => {
      if (_state.isRunning) {
        _stopExecution();
      } else {
        _startExecution();
      }
    });

    // Reset button
    els.resetBtn.addEventListener('click', _onReset);
  }

  // ── File selected ─────────────────────────────────────────────────

  function _onFileSelected(file) {
    if (!file.type.startsWith('image/')) {
      UI.showToast('Please select an image file (JPEG or PNG).', 'error');
      return;
    }
    _state.selectedFile = file;
    UI.showImagePreview(file);
    UI.setAnalyzeBtnEnabled(true);
    UI.setStatus('idle', 'Image loaded — click Analyze');
    UI.showToast('Image ready! Click "Analyze Blocks" 🔍', 'info');
  }

  // ── Analyze ───────────────────────────────────────────────────────

  async function _onAnalyze() {
    if (!_state.selectedFile) return;

    UI.setStatus('loading', 'Analyzing…');
    UI.setAnalyzeBtnEnabled(false);
    UI.showToast('Scanning for code blocks… 🔍', 'info');

    try {
      const result = await API.analyzeImage(_state.selectedFile);

      if (!result.success || result.steps.length === 0) {
        const msg = result.error || 'No blocks detected. Try again with better lighting.';
        UI.showToast(msg, 'error', 5000);
        UI.setStatus('error', 'No blocks found');
        return;
      }

      _state.steps = result.steps;
      UI.renderChips(result.raw_blocks);
      UI.renderProgramList(result.steps);
      UI.setRunBtnEnabled(true);
      UI.setStatus('success', `${result.steps.length} step(s) ready`);
      UI.showToast(`Found ${result.steps.length} steps! Press ▶ Run 🐱`, 'success');

    } catch (err) {
      UI.showToast(`Error: ${err.message}`, 'error', 6000);
      UI.setStatus('error', 'Analysis failed');
      console.error('[App] Analyze error:', err);
    } finally {
      UI.setAnalyzeBtnEnabled(true);
    }
  }

  // ── Execution ─────────────────────────────────────────────────────

  function _startExecution() {
    if (!_state.steps.length) return;
    _state.isRunning = true;
    UI.setRunBtnLabel('<span>⏹</span> Stop');
    UI.setStatus('running', 'Running…');

    _state.activeWs = API.executeProgram(_state.steps, {
      onReset: () => {
        Stage.reset();
        UI.hideStepCounter();
        console.log('[App] Stage reset by server.');
      },
      onStep: ({ stepIndex, action, totalSteps }) => {
        Stage.step(action);
        UI.highlightStep(stepIndex);
        UI.showStepCounter(stepIndex + 1, totalSteps);
      },
      onDone: ({ totalSteps }) => {
        Stage.celebrate();
        UI.markAllDone();
        UI.showStepCounter(totalSteps, totalSteps);
        UI.showToast('🎉 Program finished! Great job!', 'success', 4000);
        UI.setStatus('success', 'Done!');
        _resetRunState();
      },
      onError: (msg) => {
        UI.showToast(`WebSocket error: ${msg}`, 'error');
        UI.setStatus('error', 'Connection error');
        _resetRunState();
      },
    });
  }

  function _stopExecution() {
    _state.activeWs?.close();
    _resetRunState();
    UI.setStatus('idle', 'Stopped');
    UI.showToast('Execution stopped.', 'info');
  }

  function _resetRunState() {
    _state.isRunning = false;
    _state.activeWs = null;
    UI.setRunBtnLabel('<span>▶</span> Run');
  }

  // ── Reset ─────────────────────────────────────────────────────────

  function _onReset() {
    if (_state.isRunning) _stopExecution();
    Stage.reset();
    _state.steps = [];
    _state.selectedFile = null;
    UI.clearImagePreview();
    UI.setAnalyzeBtnEnabled(false);
    UI.setRunBtnEnabled(false);
    UI.hideStepCounter();
    UI.renderProgramList([]);
    UI.els.sequenceBox.hidden = true;
    UI.setStatus('idle', 'Ready');
    // Clear file input so same file can be re-selected
    UI.els.fileInput.value = '';
  }

  return { init };
})();

// ── Bootstrap ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => App.init());
