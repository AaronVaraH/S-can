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
          dark: '#080c14',
          surface: '#0f172a',
          card: '#111c30',
          border: '#1e293b',
          cyan: '#06b6d4',
          emerald: '#10b981',
          crimson: '#ef4444',
          amber: '#f59e0b',
        }
      },
      animation: {
        'scanline': 'scan 2.5s ease-in-out infinite alternate',
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(0%)', opacity: '0.8' },
          '50%': { opacity: '1' },
          '100%': { transform: 'translateY(100%)', opacity: '0.8' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1', filter: 'drop-shadow(0 0 12px rgba(16, 185, 129, 0.6))' },
          '50%': { opacity: '0.6', filter: 'drop-shadow(0 0 2px rgba(16, 185, 129, 0.2))' },
        }
      }
    },
  },
  plugins: [],
}

