/**
 * bluetooth.js — Web Bluetooth API ile HC-06 iletişimi.
 *
 * HC-06 bir BLE (Bluetooth Low Energy) değil, klasik SPP cihazıdır.
 * Web Bluetooth API sadece BLE destekler.
 * Bu yüzden HC-06 için Web Serial API kullanıyoruz (USB/Serial üzerinden)
 * VEYA kullanıcı telefonda bir BLE köprü uygulaması kullanır.
 *
 * Strateji:
 *   1. Web Serial API (Chrome masaüstü — USB veya Serial adapter)
 *   2. Web Bluetooth API (BLE modül kullanılıyorsa — HC-10, HM-10)
 *   3. Manuel mod — komutları ekranda göster, kullanıcı kopyalar
 *
 * HC-06 ile en pratik: bilgisayara Bluetooth klasik ile eşleştir,
 * sonra COM port olarak Web Serial ile bağlan.
 */

const Bluetooth = (() => {
  let _port   = null;   // Web Serial port
  let _writer = null;   // WritableStreamDefaultWriter
  let _isConnected = false;
  let _onStatusChange = null;

  // ── Komut haritası ─────────────────────────────────────────────
  // Backend'den gelen action string → Arduino komut karakteri
  const ACTION_TO_CMD = {
    move_up:    '1',   // İleri
    move_down:  '2',   // Geri
    move_left:  '4',   // Sol
    move_right: '3',   // Sağ
  };

  const STOP_CMD  = '5';
  const STEP_MS   = 600;   // Her adım kaç ms sürer (Arduino ile eşleşmeli)
  const PAUSE_MS  = 150;   // Adımlar arası duraklatma

  // ── Bağlantı ───────────────────────────────────────────────────

  async function connect() {
    if (!('serial' in navigator)) {
      throw new Error(
        'Web Serial API desteklenmiyor. Chrome 89+ masaüstü gerekli. ' +
        'chrome://flags/#enable-experimental-web-platform-features aktif et.'
      );
    }

    try {
      _port = await navigator.serial.requestPort();
      await _port.open({ baudRate: 9600 });

      const encoder = new TextEncoderStream();
      encoder.readable.pipeTo(_port.writable);
      _writer = encoder.writable.getWriter();

      _isConnected = true;
      _onStatusChange?.('connected');
      return true;
    } catch (err) {
      _isConnected = false;
      _onStatusChange?.('disconnected');
      throw err;
    }
  }

  async function disconnect() {
    try {
      if (_writer) { await _writer.close(); _writer = null; }
      if (_port)   { await _port.close();   _port   = null; }
    } catch (_) {}
    _isConnected = false;
    _onStatusChange?.('disconnected');
  }

  // ── Komut gönderme ─────────────────────────────────────────────

  async function sendChar(char) {
    if (!_writer) throw new Error('Bağlı değil.');
    await _writer.write(char);
  }

  /**
   * Adım listesini sırayla robota gönder.
   * Her adım: komut gönder → STEP_MS bekle → dur gönder → PAUSE_MS bekle
   *
   * @param {Array<{action:string}>} steps
   * @param {Function} onStep - (index, action) => void  ilerleme callback'i
   */
  async function executeSteps(steps, onStep) {
    if (!_isConnected) throw new Error('Robot bağlı değil!');

    for (let i = 0; i < steps.length; i++) {
      const action = steps[i].action;
      const cmd    = ACTION_TO_CMD[action];

      if (!cmd) {
        console.warn('Bluetooth: bilinmeyen action atlandı:', action);
        continue;
      }

      onStep?.(i, action);

      // Komutu gönder
      await sendChar(cmd);
      // Hareket süresi kadar bekle
      await _sleep(STEP_MS);
      // Durdur
      await sendChar(STOP_CMD);
      // Sonraki adım öncesi kısa bekleme
      await _sleep(PAUSE_MS);
    }

    // Program bitti — emin olmak için tekrar dur
    await sendChar(STOP_CMD);
  }

  function _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ── Public ─────────────────────────────────────────────────────

  function onStatusChange(cb) { _onStatusChange = cb; }
  function isConnected()      { return _isConnected; }
  function getStepMs()        { return STEP_MS; }
  function setStepMs(ms)      { /* STEP_MS = ms; */ }  // runtime ayar için

  return {
    connect, disconnect, executeSteps,
    onStatusChange, isConnected,
    ACTION_TO_CMD, STOP_CMD,
  };
})();
