/**
 * 设计令牌来源：stitch 导出的 DESIGN.md
 * 正文声明过的 13 个色值全部落在这里，保证代码与设计文档一一对应。
 */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        // 表面层次
        canvas:   '#121316',
        surface:  '#1f1f23',
        overlay:  '#26282d',
        hover:    '#292a2d',
        divider:  '#2b2d30',
        edge:     '#393b40',
        // 文字灰阶
        ink:      '#e2e2e6',
        muted:    '#8c8f99',
        dim:      '#555861',
        // 语义色
        primary:  '#b1c5ff',
        success:  '#87d894',
        danger:   '#ffb4ab',
        warning:  '#ffb77c',
        ai:       '#e8b3ff',
      },
      fontFamily: {
        // 不引 CDN，优先本地字体，回落到系统字体
        sans: ['Geist', 'Inter', 'system-ui', '-apple-system', 'Segoe UI',
               'Microsoft YaHei', 'PingFang SC', 'sans-serif'],
        mono: ['JetBrains Mono', 'Cascadia Code', 'Consolas', 'SF Mono',
               'Menlo', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        '2xs': ['11px', '14px'],
      },
      borderRadius: {
        badge: '2px',
        ctl:   '4px',
        card:  '8px',
      },
      spacing: {
        row: '28px',
      },
      boxShadow: {
        float: '0 4px 12px rgba(0,0,0,0.6)',
      },
    },
  },
  plugins: [],
}
