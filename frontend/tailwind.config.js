/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary - Metall ko'k
        primary: {
          DEFAULT: '#1E40AF',
          dark: '#1E3A8A',
          light: '#3B82F6',
        },
        // Accent / Success - Yashil
        success: {
          DEFAULT: '#059669',
          light: '#10B981',
          dark: '#047857',
        },
        // Warning - To'q sariq
        warning: {
          DEFAULT: '#D97706',
          light: '#F59E0B',
          dark: '#B45309',
        },
        // Danger - Qizil
        danger: {
          DEFAULT: '#DC2626',
          light: '#EF4444',
          dark: '#B91C1C',
        },
        // Neutrals
        background: '#F8FAFC',
        surface: '#FFFFFF',
        border: '#E2E8F0',
        // Text
        'text-primary': '#0F172A',
        'text-secondary': '#64748B',
      },
      fontSize: {
        // Katta shriftlar - qariyalar uchun
        'pos-sm': ['18px', '24px'],
        'pos-base': ['20px', '28px'],
        'pos-lg': ['24px', '32px'],
        'pos-xl': ['28px', '36px'],
        'pos-2xl': ['36px', '44px'],
        'pos-total': ['48px', '56px'],
      },
      spacing: {
        // Katta padding/margin
        'pos': '16px',
        'pos-lg': '24px',
      },
      minHeight: {
        'btn': '48px',
        'btn-lg': '60px',
        'btn-xl': '80px',
      },
      borderRadius: {
        'pos': '12px',
      },
    },
  },
  plugins: [],
}
