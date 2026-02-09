/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'steel-blue': '#4A7C9B',
        'iron': '#3D3D3D',
        'forge-orange': '#E8722A',
        'navy': '#1B2A4A',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
