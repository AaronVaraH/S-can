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
        dark: {
          950: '#070b12',
          900: '#0b111e',
          850: '#0f1728',
          800: '#152136',
          700: '#1e2f4d',
        },
        accent: {
          blue: '#3b82f6',
          cyan: '#0ea5e9',
          emerald: '#10b981',
          rose: '#f43f5e',
          amber: '#f59e0b',
        }
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.36)',
        'glass-sm': '0 4px 16px 0 rgba(0, 0, 0, 0.25)',
        'glass-glow': '0 0 24px -4px rgba(14, 165, 233, 0.15)',
        'inner-specular': 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.12)',
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

