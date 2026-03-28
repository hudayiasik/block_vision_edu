/**
 * api.js — all HTTP + WebSocket communication.
 *
 * Module pattern: exposes a single `API` namespace.
 * Zero dependencies on other JS files except config.js.
 */

const API = (() => {
  // ── HTTP ─────────────────────────────────────────────────────────

  /**
   * POST /api/analyze-image
   * @param {File} file - JPEG or PNG image file
   * @returns {Promise<{success, steps, raw_blocks, error}>}
   */
  async function analyzeImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${CONFIG.API_BASE_URL}/api/analyze-image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // ── WebSocket ─────────────────────────────────────────────────────

  /**
   * Connect to the execution WebSocket and stream steps.
   *
   * @param {Object[]} steps - Array of StepSchema objects
   * @param {Object}   handlers
   * @param {Function} handlers.onReset  - () => void
   * @param {Function} handlers.onStep   - ({ stepIndex, action, totalSteps }) => void
   * @param {Function} handlers.onDone   - ({ totalSteps }) => void
   * @param {Function} handlers.onError  - (message) => void
   * @returns {WebSocket} - caller can close early if needed
   */
  function executeProgram(steps, { onReset, onStep, onDone, onError }) {
    const ws = new WebSocket(CONFIG.WS_URL);

    ws.addEventListener('open', () => {
      ws.send(JSON.stringify({ steps }));
    });

    ws.addEventListener('message', (event) => {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
        console.warn('Non-JSON WS message:', event.data);
        return;
      }

      switch (msg.event) {
        case 'reset': onReset?.(); break;
        case 'step':
          onStep?.({
            stepIndex: msg.step_index,
            action: msg.action,
            totalSteps: msg.total_steps,
          });
          break;
        case 'done': onDone?.({ totalSteps: msg.total_steps }); break;
        case 'error': onError?.(msg.message); break;
        default: console.warn('Unknown WS event:', msg.event);
      }
    });

    ws.addEventListener('error', (e) => {
      onError?.('WebSocket connection failed. Is the server running?');
    });

    return ws;
  }

  return { analyzeImage, executeProgram };
})();
