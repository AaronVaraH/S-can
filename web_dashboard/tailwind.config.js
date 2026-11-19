/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      colors: {
        brand: {
          ice: '#E5F0FE',       // Reflejo Óptico Hielo (L=0.861)
          silver: '#BFC2C4',    // Aluminio Cepillado (L=0.536)
          sand: '#B7A181',      // Champagne / Oro Arena (L=0.371)
          brass: '#A88C5D',     // Latón Industrial / Bronce (L=0.279)
          umber: '#4A4036',     // Café / Carbón Bronceado para resaltar (L=0.054)
          800: '#181B22',       // Superficie elevada Neutral Dark
          900: '#111318',       // Panel base Neutral Dark
          950: '#0B0D10',       // Fondo profundo Neutral Dark
        },
        skin: {
          app: 'var(--bg-app)',
          panel: 'var(--bg-panel)',
          card: 'var(--bg-card)',
          elevated: 'var(--bg-elevated)',
          input: 'var(--bg-input)',
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
          accent: 'var(--accent-primary)',
          brass: 'var(--accent-secondary)',
        }
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(18, 16, 14, 0.28)',
        'glass-sm': '0 4px 16px 0 rgba(18, 16, 14, 0.18)',
        'glass-glow': '0 0 24px -4px rgba(183, 161, 129, 0.22)',
        'inner-specular': 'inset 0 1px 1px 0 rgba(229, 240, 254, 0.12)',
      },
      backdropBlur: {
        'xs': '2px',
        'md': '12px',
        'xl': '20px',
      }
    },
  },
  plugins: [],
}

