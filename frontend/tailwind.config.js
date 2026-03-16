/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary:  { DEFAULT: '#6c63ff', dark: '#5a52e8', light: '#8b85ff' },
        success:  { DEFAULT: '#00d4aa', dark: '#00b891' },
        warning:  { DEFAULT: '#ff6b35' },
        danger:   { DEFAULT: '#ff3366', dark: '#cc2952' },
        gold:     { DEFAULT: '#ffd166' },
        surface:  { DEFAULT: '#111118', 2: '#1a1a24', 3: '#23232f' },
        border:   { DEFAULT: '#2a2a38' },
      }
    }
  },
  plugins: []
}
