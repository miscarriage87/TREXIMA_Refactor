/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // SAP-inspired color palette
        'sap-blue': {
          50: '#e6f2ff',
          100: '#cce5ff',
          200: '#99ccff',
          300: '#66b2ff',
          400: '#3399ff',
          500: '#0070f2',  // Primary SAP blue
          600: '#0059c2',
          700: '#004391',
          800: '#002c61',
          900: '#001630',
        },
        'sap-green': {
          500: '#107e3e',  // Success
        },
        'sap-orange': {
          500: '#e76500',  // Warning
        },
        'sap-red': {
          500: '#bb0000',  // Error
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
