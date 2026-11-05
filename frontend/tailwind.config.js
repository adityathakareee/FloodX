/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        flood: {
          darkest: '#070D1E',
          card: '#0D162B',
          surface: '#121F3D',
          hover: '#182A52',
          border: '#1E325F',
          cyan: '#00F0FF',
          blue: '#38BDF8',
          accent: '#0284C7',
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#EF4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      }
    },
  },
  plugins: [],
}

