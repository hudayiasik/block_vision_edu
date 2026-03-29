/**
 * api.js — HTTP + WebSocket iletişimi.
 * Her executeProgram çağrısında yeni WS bağlantısı açılır,
 * done alınınca frontend kapatır.
 */

const API = (() => {

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

  function executeProgram(steps, { onReset, onStep, onDone, onError }) {
    const ws = new WebSocket(CONFIG.WS_URL);

    ws.onopen = () => {
      ws.send(JSON.stringify({ steps }));
    };

    ws.onmessage = (event) => {
      let msg;
      try { msg = JSON.parse(event.data); } catch { return; }

      switch (msg.event) {
        case 'reset': onReset?.(); break;
        case 'step':
          onStep?.({
            stepIndex:  msg.step_index,
            action:     msg.action,
            totalSteps: msg.total_steps,
          });
          break;
        case 'done':
          onDone?.({ totalSteps: msg.total_steps });
          ws.close();
          break;
        case 'error':
          onError?.(msg.message);
          ws.close();
          break;
      }
    };

    ws.onerror = () => {
      onError?.('Sunucuya baglanamadi. Sunucu calisiyor mu?');
    };

    ws.onclose = () => {};

    return { close: () => { if (ws.readyState === WebSocket.OPEN) ws.close(); } };
  }

  function closeActive() {}

  return { analyzeImage, executeProgram, closeActive };
})();
