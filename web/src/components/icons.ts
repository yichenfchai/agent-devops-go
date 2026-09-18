/**
 * 内联 SVG 图标表。
 * 设计稿用的是 Google Material Symbols（CDN 字体），断网会退化成一串英文单词。
 * 这里全部改成内联 path 数据，零网络依赖。
 */
export const PATHS = {
  // 导航
  grid:        'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  history:     'M12 3a9 9 0 1 0 9 9M12 3v9l6 3M3 8V4h4',
  server:      'M3 4h18v6H3zM3 14h18v6H3zM7 7h.01M7 17h.01',
  key:         'M14 10a4 4 0 1 0-3.5 3.97L9 15.5V18h2.5l.5-1.5h1.5V15h1.5l.5-1.5z',
  sliders:     'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M14 4v4M8 10v4M16 16v4',
  // 操作
  search:      'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM16 16l4.5 4.5',
  play:        'M6 4l14 8-14 8z',
  plus:        'M12 5v14M5 12h14',
  close:       'M6 6l12 12M18 6L6 18',
  chevronRight:'M9 5l7 7-7 7',
  chevronDown: 'M5 9l7 7 7-7',
  more:        'M6 12h.01M12 12h.01M18 12h.01',
  refresh:     'M20 12a8 8 0 1 1-2.34-5.66M20 4v4h-4',
  download:    'M12 4v11M7 11l5 5 5-5M4 19h16',
  undo:        'M4 10h11a4 4 0 0 1 0 8H9M4 10l4-4M4 10l4 4',
  save:        'M5 4h11l3 3v13H5zM8 4v5h7V4M8 14h8v6H8z',
  eye:         'M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  stop:        'M7 7h10v10H7z',
  filter:      'M3 5h18l-7 8v6l-4 2v-8z',
  // 状态
  check:       'M5 13l4 4L19 7',
  alert:       'M12 4l9 16H3zM12 10v4M12 17h.01',
  x:           'M8 8l8 8M16 8l-8 8',
  clock:       'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM12 8v4.5l3 2',
  spinner:     'M21 12a9 9 0 1 1-6.2-8.6',
  skip:        'M6 5v14l8-7zM17 5v14',
  // 领域
  terminal:    'M3 4h18v16H3zM7 9l3 3-3 3M13 15h4',
  sparkle:     'M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9zM18 15l.9 2.1L21 18l-2.1.9L18 21l-.9-2.1L15 18l2.1-.9z',
  branch:      'M7 5a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 15a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM17 7a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 9v6M17 11v1a3 3 0 0 1-3 3H9',
  commit:      'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM3 12h5M16 12h5',
  chip:        'M8 8h8v8H8zM4 10h4M4 14h4M16 10h4M16 14h4M10 4v4M14 4v4M10 16v4M14 16v4',
  bell:        'M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6zM10 19a2 2 0 0 0 4 0',
  lock:        'M6 11h12v9H6zM9 11V8a3 3 0 0 1 6 0v3',
  fingerprint: 'M12 4a7 7 0 0 0-7 7v3M12 4a7 7 0 0 1 7 7v4M9 11a3 3 0 0 1 6 0v3M12 11v7M6 17v-6M18 15v3',
  inbox:       'M3 13l3-8h12l3 8v7H3zM3 13h5l1 2h6l1-2h5',
  cloudOff:    'M7 18a4 4 0 0 1 0-8 5.5 5.5 0 0 1 10.5 1.5A3.5 3.5 0 0 1 17 18zM4 4l16 16',
  hourglass:   'M7 3h10L12 11zM7 21h10L12 13z',
  shield:      'M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6z',
  user:        'M12 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM4 21a8 8 0 0 1 16 0',
  info:        'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM12 11v5M12 8h.01',
  rocket:      'M14 4c4 1 6 3 6 6l-4 2-4 4-2 4c-3 0-5-2-6-6l4-2zM5 19l3-3',
  folder:      'M3 6h6l2 2h10v11H3z',
  code:        'M9 6l-5 6 5 6M15 6l5 6-5 6',
} as const

export type IconName = keyof typeof PATHS
