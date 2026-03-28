/**
 * config.js — front-end configuration constants.
 *
 * Single source of truth for all magic values.
 * Adjust API_BASE_URL when deploying to a real server.
 */

const CONFIG = Object.freeze({
  /** Backend origin (same-origin in production, explicit in dev) */
  API_BASE_URL: window.location.origin,

  /** WebSocket endpoint */
  WS_URL: `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/execute`,

  /** Grid dimensions (must match CSS --grid-cells) */
  GRID_CELLS: 8,
  CELL_PX: 60,                  // pixels per grid cell on the cat stage

  /** Starting grid position for the cat (0-indexed) */
  CAT_START_COL: 3,
  CAT_START_ROW: 3,

  /** Milliseconds the frontend waits before starting next step */
  STEP_DELAY_MS: 600,

  /** Block type → display metadata */
  BLOCK_META: {
    start:      { icon: '🟢', label: 'Start',      color: '#52C41A' },
    move_up:    { icon: '⬆️',  label: 'Move Up',    color: '#4A90D9' },
    move_down:  { icon: '⬇️',  label: 'Move Down',  color: '#F5222D' },
    move_left:  { icon: '⬅️',  label: 'Move Left',  color: '#FAAD14' },
    move_right: { icon: '➡️',  label: 'Move Right', color: '#722ED1' },
    loop_start: { icon: '🔁',  label: 'Loop Start', color: '#FA8C16' },
    loop_end:   { icon: '🔚',  label: 'Loop End',   color: '#EB2F96' },
    unknown:    { icon: '❓',  label: 'Unknown',    color: '#ADB5BD' },
  },

  /** HSV color guide shown to the user */
  COLOR_GUIDE: [
    { type: 'start',      label: 'Start',       color: '#52C41A' },
    { type: 'move_up',    label: 'Move Up',      color: '#4A90D9' },
    { type: 'move_down',  label: 'Move Down',    color: '#E03030' },
    { type: 'move_left',  label: 'Move Left',    color: '#FADB14' },
    { type: 'move_right', label: 'Move Right',   color: '#722ED1' },
    { type: 'loop_start', label: 'Loop Start',   color: '#FA8C16' },
    { type: 'loop_end',   label: 'Loop End',     color: '#EB2F96' },
  ],
});
