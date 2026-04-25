/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#dce8ff',
          500: '#4f7cff',
          600: '#3a65f5',
          700: '#2a4fe0',
        },
      },
    },
  },
  plugins: [],
}
