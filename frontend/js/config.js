/**
 * config.js — tüm sabitler tek yerde.
 *
 * Yeni blok tipi eklemek için sadece BLOCK_META ve COLOR_GUIDE'a ekle.
 * Yeni stage eklemek için sadece STAGES dizisine ekle.
 */

const CONFIG = Object.freeze({
  API_BASE_URL: window.location.origin,
  WS_URL: `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/execute`,

  CELL_PX: 60,
  STEP_DELAY_MS: 550,

  // Genişletilebilir blok meta — if_start, sound, vb. buraya eklenecek
  BLOCK_META: {
    start:      { icon: '▶',  label: 'Başlat',     color: '#2D8A3E' },
    move_up:    { icon: '↑',  label: 'Yukarı',     color: '#1E6DC0' },
    move_down:  { icon: '↓',  label: 'Aşağı',      color: '#C0241E' },
    move_left:  { icon: '←',  label: 'Sol',         color: '#B8860B' },
    move_right: { icon: '→',  label: 'Sağ',         color: '#5E20B8' },
    loop_start: { icon: '↺',  label: 'Döngü',       color: '#C45D00' },
    loop_end:   { icon: '■',  label: 'Döngü Bitti', color: '#B01870' },
    // Gelecek bloklar — şimdilik devre dışı, backend'e eklenince aktif olur:
    // if_start:   { icon: '?',  label: 'Eğer',        color: '#0E7490' },
    // if_end:     { icon: '!',  label: 'Eğer Bitti',  color: '#0E7490' },
    // sound:      { icon: '♪',  label: 'Ses Çal',     color: '#7C3AED' },
    unknown:    { icon: '?',  label: 'Bilinmiyor',  color: '#888' },
  },

  // ── Stage tanımları ─────────────────────────────────────────────
  // Yeni stage eklemek = bu diziye bir nesne eklemek
  STAGES: [
    {
      id: 1,
      title: 'İlk Adım',
      description: 'Kediyi 3 kez yukarı yürüt!',
      emoji: '🐾',
      gridSize: 6,
      catStart: { col: 2, row: 4 },
      target:   { col: 2, row: 1 },
      walls: [],
      hint: 'Yukarı bloğunu 3 kez sıraya koy.',
    },
    {
      id: 2,
      title: 'Köşeye Yürü',
      description: 'Kediyi hedefe ulaştır!',
      emoji: '⭐',
      gridSize: 6,
      catStart: { col: 0, row: 5 },
      target:   { col: 4, row: 1 },
      walls: [],
      hint: 'Önce sağa, sonra yukarı git.',
    },
    {
      id: 3,
      title: 'Engelden Geç',
      description: 'Duvarları aşarak hedefe ulaş!',
      emoji: '🧱',
      gridSize: 7,
      catStart: { col: 0, row: 6 },
      target:   { col: 6, row: 0 },
      walls: [
        { col: 2, row: 1 }, { col: 2, row: 2 }, { col: 2, row: 3 },
        { col: 2, row: 4 }, { col: 4, row: 2 }, { col: 4, row: 3 },
        { col: 4, row: 4 }, { col: 4, row: 5 },
      ],
      hint: 'Duvarların arasından geçmen gerekiyor.',
    },
    {
      id: 4,
      title: 'Döngü Vakti',
      description: 'Loop bloğunu kullanmadan çok uzun!',
      emoji: '🔁',
      gridSize: 8,
      catStart: { col: 0, row: 7 },
      target:   { col: 0, row: 1 },
      walls: [],
      hint: 'Döngü bloğuyla çok daha az blok kullanabilirsin!',
      loopRequired: true,
    },
    {
      id: 5,
      title: 'Labirent',
      description: 'Karmaşık labirentten çık!',
      emoji: '🌀',
      gridSize: 8,
      catStart: { col: 0, row: 7 },
      target:   { col: 7, row: 0 },
      walls: [
        { col: 1, row: 5 }, { col: 1, row: 6 },
        { col: 3, row: 2 }, { col: 3, row: 3 }, { col: 3, row: 4 }, { col: 3, row: 5 },
        { col: 5, row: 1 }, { col: 5, row: 2 }, { col: 5, row: 3 },
        { col: 2, row: 0 }, { col: 2, row: 1 },
        { col: 6, row: 4 }, { col: 6, row: 5 }, { col: 6, row: 6 },
      ],
      hint: 'Dikkatli planla, döngüler işine yarayabilir.',
    },
    {
      id: 6,
      title: 'Büyük Harita',
      description: 'Geniş alanda istediğin yere git!',
      emoji: '🗺️',
      gridSize: 10,
      catStart: { col: 0, row: 9 },
      target:   { col: 9, row: 0 },
      walls: [
        { col: 2, row: 7 }, { col: 2, row: 8 },
        { col: 4, row: 4 }, { col: 4, row: 5 }, { col: 4, row: 6 },
        { col: 6, row: 2 }, { col: 6, row: 3 }, { col: 6, row: 4 },
        { col: 8, row: 6 }, { col: 8, row: 7 }, { col: 8, row: 8 },
      ],
      hint: 'Döngü ve yön bloklarını birlikte kullan.',
    },
  ],

  // Tile tipleri — map render için
  TILE: {
    GRASS:  'grass',
    WATER:  'water',
    STONE:  'stone',
    FLOWER: 'flower',
    TREE:   'tree',
    WALL:   'wall',
  },
});
