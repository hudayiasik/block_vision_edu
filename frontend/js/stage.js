/**
 * stage.js — tile map + kedi sprite kontrolcüsü.
 *
 * Sorumluluklar:
 *   - Tile map render (çimen, su, taş, çiçek, ağaç, duvar)
 *   - Kedi hareketi ve animasyonu
 *   - Hedef ve duvar çarpışma kontrolü
 *   - Mobilde ekranı kediye kilitleme
 *
 * Dışarıya bağımlılık yok — sadece CONFIG okur.
 */

const Stage = (() => {
  let _stage = null;
  let _catEl = null;
  let _currentStage = null;
  let _col = 0;
  let _row = 0;
  let _tileMap = [];
  let _onWallHit = null;
  let _onTargetReached = null;

  const DELTA = {
    move_up:    [  0, -1 ],
    move_down:  [  0,  1 ],
    move_left:  [ -1,  0 ],
    move_right: [  1,  0 ],
  };

  // ── Tile üretici ────────────────────────────────────────────────

  function _seedRandom(x, y, stageId) {
    const n = Math.sin(x * 374761393 + y * 668265263 + stageId * 2246822519) * 43758.5453;
    return n - Math.floor(n);
  }

  function _generateTileMap(stageData) {
    const s = stageData.gridSize;
    const wallSet = new Set(stageData.walls.map(w => `${w.col},${w.row}`));
    const map = [];
    const TILES = ['grass','grass','grass','grass','flower','stone'];

    for (let r = 0; r < s; r++) {
      map[r] = [];
      for (let c = 0; c < s; c++) {
        if (wallSet.has(`${c},${r}`)) {
          map[r][c] = 'wall';
        } else {
          const rnd = _seedRandom(c, r, stageData.id);
          map[r][c] = TILES[Math.floor(rnd * TILES.length)];
        }
      }
    }
    return map;
  }

  // ── Render ──────────────────────────────────────────────────────

  const TILE_EMOJI = {
    grass:  ['🌿','🌱','🍀','🌾'],
    flower: ['🌸','🌼','🌻','💐'],
    stone:  ['🪨','⬛','🔘'],
    wall:   ['🧱'],
  };

  function _tileChar(type, col, row, stageId) {
    const arr = TILE_EMOJI[type] || ['🌿'];
    const idx = Math.floor(_seedRandom(col + 0.5, row + 0.7, stageId) * arr.length);
    return arr[idx];
  }

  function _render(stageData) {
    _stage.innerHTML = '';
    const s = stageData.gridSize;
    const cellPx = CONFIG.CELL_PX;

    _stage.style.width  = `${s * cellPx}px`;
    _stage.style.height = `${s * cellPx}px`;
    _stage.style.position = 'relative';

    const wallSet = new Set(stageData.walls.map(w => `${w.col},${w.row}`));

    for (let r = 0; r < s; r++) {
      for (let c = 0; c < s; c++) {
        const tile = document.createElement('div');
        tile.className = 'tile';
        tile.style.cssText = `
          position:absolute;
          left:${c * cellPx}px;
          top:${r * cellPx}px;
          width:${cellPx}px;
          height:${cellPx}px;
          display:flex;
          align-items:center;
          justify-content:center;
          font-size:${cellPx * 0.55}px;
          user-select:none;
          border:1px solid rgba(0,0,0,0.06);
          box-sizing:border-box;
          background: ${_tileBackground(_tileMap[r][c])};
        `;

        if (wallSet.has(`${c},${r}`)) {
          tile.textContent = '🧱';
          tile.style.background = '#8B6914';
        } else {
          tile.textContent = _tileChar(_tileMap[r][c], c, r, stageData.id);
        }

        tile.dataset.col = c;
        tile.dataset.row = r;
        _stage.appendChild(tile);
      }
    }

    // Hedef
    _renderTarget(stageData);

    // Kedi
    _catEl = document.createElement('div');
    _catEl.id = 'cat-sprite';
    _catEl.style.cssText = `
      position:absolute;
      width:${cellPx - 4}px;
      height:${cellPx - 4}px;
      z-index:20;
      transition: left 0.4s cubic-bezier(0.34,1.56,0.64,1),
                  top  0.4s cubic-bezier(0.34,1.56,0.64,1);
      font-size:${cellPx * 0.7}px;
      display:flex;
      align-items:center;
      justify-content:center;
      filter:drop-shadow(2px 3px 4px rgba(0,0,0,0.3));
    `;
    _catEl.innerHTML = _catSVG();
    _stage.appendChild(_catEl);
  }

  function _tileBackground(type) {
    const map = {
      grass:  '#4CAF50',
      flower: '#66BB6A',
      stone:  '#78909C',
      wall:   '#8B6914',
    };
    return map[type] || '#4CAF50';
  }

  function _renderTarget(stageData) {
    const old = _stage.querySelector('.target-cell');
    if (old) old.remove();

    const t = stageData.target;
    const target = document.createElement('div');
    target.className = 'target-cell';
    target.style.cssText = `
      position:absolute;
      left:${t.col * CONFIG.CELL_PX}px;
      top:${t.row * CONFIG.CELL_PX}px;
      width:${CONFIG.CELL_PX}px;
      height:${CONFIG.CELL_PX}px;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:${CONFIG.CELL_PX * 0.6}px;
      z-index:10;
      animation: targetPulse 1.2s ease-in-out infinite;
    `;
    target.textContent = '⭐';
    _stage.appendChild(target);
  }

  function _catSVG() {
    return `<svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%">
      <ellipse cx="40" cy="52" rx="22" ry="18" fill="#FFA03C"/>
      <circle cx="40" cy="30" r="18" fill="#FFA03C"/>
      <polygon points="24,18 20,6 32,14" fill="#FFA03C"/>
      <polygon points="56,18 60,6 48,14" fill="#FFA03C"/>
      <polygon points="25,17 22,9 31,14" fill="#FF8C69"/>
      <polygon points="55,17 58,9 49,14" fill="#FF8C69"/>
      <ellipse cx="33" cy="27" rx="5" ry="6" fill="white"/>
      <ellipse cx="47" cy="27" rx="5" ry="6" fill="white"/>
      <circle cx="34" cy="28" r="3" fill="#1E1E1E"/>
      <circle cx="48" cy="28" r="3" fill="#1E1E1E"/>
      <circle cx="35" cy="27" r="1" fill="white"/>
      <circle cx="49" cy="27" r="1" fill="white"/>
      <ellipse cx="40" cy="34" rx="3" ry="2" fill="#FF7A7A"/>
      <path d="M37,36 Q40,39 43,36" stroke="#c0453a" stroke-width="1.2" fill="none" stroke-linecap="round"/>
      <line x1="20" y1="33" x2="35" y2="34" stroke="#888" stroke-width="0.8"/>
      <line x1="20" y1="36" x2="35" y2="36" stroke="#888" stroke-width="0.8"/>
      <line x1="45" y1="34" x2="60" y2="33" stroke="#888" stroke-width="0.8"/>
      <line x1="45" y1="36" x2="60" y2="36" stroke="#888" stroke-width="0.8"/>
      <path d="M60,58 Q80,48 74,38" stroke="#FFA03C" stroke-width="6" fill="none" stroke-linecap="round"/>
      <ellipse cx="40" cy="54" rx="12" ry="10" fill="#FFDCA8"/>
      <ellipse cx="28" cy="68" rx="8" ry="5" fill="#FFA03C"/>
      <ellipse cx="52" cy="68" rx="8" ry="5" fill="#FFA03C"/>
    </svg>`;
  }

  // ── Pozisyon ─────────────────────────────────────────────────────

  function _applyPosition(animate) {
    if (!_catEl) return;
    const left = _col * CONFIG.CELL_PX + 2;
    const top  = _row * CONFIG.CELL_PX + 2;
    _catEl.style.left = `${left}px`;
    _catEl.style.top  = `${top}px`;

    if (animate) {
      _catEl.classList.remove('hop');
      void _catEl.offsetWidth;
      _catEl.classList.add('hop');
      // Mobil: ekranı kediye kilitle
      _scrollToCat();
    }
  }

  function _scrollToCat() {
    if (!_catEl) return;
    const stageWrapper = document.getElementById('stage-wrapper');
    if (!stageWrapper) return;
    const catRect = _catEl.getBoundingClientRect();
    const wrapRect = stageWrapper.getBoundingClientRect();
    const scrollTop = stageWrapper.scrollTop + catRect.top - wrapRect.top
                      - stageWrapper.clientHeight / 2 + CONFIG.CELL_PX / 2;
    const scrollLeft = stageWrapper.scrollLeft + catRect.left - wrapRect.left
                       - stageWrapper.clientWidth / 2 + CONFIG.CELL_PX / 2;
    stageWrapper.scrollTo({ top: scrollTop, left: scrollLeft, behavior: 'smooth' });
  }

  function _isWall(c, r) {
    if (!_currentStage) return false;
    const s = _currentStage.gridSize;
    if (c < 0 || r < 0 || c >= s || r >= s) return true;
    return (_tileMap[r] && _tileMap[r][c] === 'wall');
  }

  // ── Public API ────────────────────────────────────────────────────

  function init(stageEl, stageData, { onWallHit, onTargetReached } = {}) {
    _stage = stageEl;
    _currentStage = stageData;
    _onWallHit = onWallHit || null;
    _onTargetReached = onTargetReached || null;
    _tileMap = _generateTileMap(stageData);
    _render(stageData);
    _col = stageData.catStart.col;
    _row = stageData.catStart.row;
    _applyPosition(false);
    _scrollToCat();
  }

  function reset() {
    if (!_currentStage) return;
    _col = _currentStage.catStart.col;
    _row = _currentStage.catStart.row;
    if (_catEl) {
      _catEl.classList.remove('hop', 'celebrate', 'shake');
      _catEl.querySelector('svg').style.transform = 'scaleX(1)';
    }
    _renderTarget(_currentStage);
    _applyPosition(false);
  }

  function step(action) {
    const delta = DELTA[action];
    if (!delta || !_currentStage) return;

    const nextCol = _col + delta[0];
    const nextRow = _row + delta[1];

    if (_isWall(nextCol, nextRow)) {
      // Duvara çarptı
      if (_catEl) {
        _catEl.classList.remove('shake');
        void _catEl.offsetWidth;
        _catEl.classList.add('shake');
        // Haptic feedback (destekleyen cihazlarda)
        if (navigator.vibrate) navigator.vibrate([30, 10, 30]);
      }
      _onWallHit && _onWallHit();
      return;
    }

    _col = nextCol;
    _row = nextRow;

    // Yön çevir
    if (_catEl) {
      _catEl.querySelector('svg').style.transform =
        action === 'move_left' ? 'scaleX(-1)' : 'scaleX(1)';
    }

    _applyPosition(true);

    // Hedefe ulaştı mı?
    const t = _currentStage.target;
    if (_col === t.col && _row === t.row) {
      setTimeout(() => {
        celebrate();
        // Haptic başarı
        if (navigator.vibrate) navigator.vibrate([50, 30, 100]);
        _onTargetReached && _onTargetReached();
      }, 420);
    }
  }

  function celebrate() {
    if (!_catEl) return;
    _catEl.classList.remove('celebrate');
    void _catEl.offsetWidth;
    _catEl.classList.add('celebrate');
  }

  function getPosition() { return { col: _col, row: _row }; }

  return { init, reset, step, celebrate, getPosition };
})();
