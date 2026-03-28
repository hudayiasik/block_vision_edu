/**
 * stage.js — cat sprite controller.
 *
 * Responsible ONLY for the cat's position/animation.
 * No networking, no DOM outside the stage element.
 *
 * Single Responsibility: move the cat.
 */

const Stage = (() => {
  const catEl = document.getElementById('cat-sprite');
  const stageEl = document.getElementById('stage');

  // Current grid position
  let col = CONFIG.CAT_START_COL;
  let row = CONFIG.CAT_START_ROW;

  /** Direction maps: action → [deltaCol, deltaRow] */
  const DELTA = {
    move_up:    [  0, -1 ],
    move_down:  [  0,  1 ],
    move_left:  [ -1,  0 ],
    move_right: [  1,  0 ],
  };

  // ── Private ───────────────────────────────────────────────────────

  function _clamp(val, min, max) {
    return Math.max(min, Math.min(max, val));
  }

  /**
   * Convert grid (col, row) to pixel (left, top) for the sprite.
   * Centers the sprite within the cell.
   */
  function _gridToPixel(c, r) {
    const spriteSize = 72;
    const offset = (CONFIG.CELL_PX - spriteSize) / 2;
    return {
      left: c * CONFIG.CELL_PX + offset,
      top:  r * CONFIG.CELL_PX + offset,
    };
  }

  function _applyPosition(animate = true) {
    const { left, top } = _gridToPixel(col, row);
    catEl.style.left = `${left}px`;
    catEl.style.top  = `${top}px`;

    if (animate) {
      // Trigger CSS hop animation
      catEl.classList.remove('hop');
      void catEl.offsetWidth; // force reflow
      catEl.classList.add('hop');
    }
  }

  function _flipCat(action) {
    // Mirror cat horizontally when moving left
    catEl.querySelector('svg').style.transform =
      action === 'move_left' ? 'scaleX(-1)' : 'scaleX(1)';
  }

  // ── Public API ────────────────────────────────────────────────────

  /** Teleport cat to start position with no animation. */
  function reset() {
    col = CONFIG.CAT_START_COL;
    row = CONFIG.CAT_START_ROW;
    catEl.classList.remove('hop', 'celebrate');
    catEl.querySelector('svg').style.transform = 'scaleX(1)';
    _applyPosition(false);
  }

  /**
   * Execute one action step.
   * @param {string} action - e.g. "move_up"
   */
  function step(action) {
    const delta = DELTA[action];
    if (!delta) {
      console.warn('Stage: unknown action:', action);
      return;
    }

    const maxCell = CONFIG.GRID_CELLS - 1;
    col = _clamp(col + delta[0], 0, maxCell);
    row = _clamp(row + delta[1], 0, maxCell);

    _flipCat(action);
    _applyPosition(true);
  }

  /** Play the "all done!" celebrate animation. */
  function celebrate() {
    catEl.classList.remove('celebrate');
    void catEl.offsetWidth;
    catEl.classList.add('celebrate');
  }

  /** Initialize cat at start position when page loads. */
  function init() {
    reset();
  }

  return { init, reset, step, celebrate };
})();
