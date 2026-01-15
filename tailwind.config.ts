import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
        heading: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        background: {
          DEFAULT: '#050505',
          paper: '#0A0A0F',
          subtle: '#12121A',
        },
        foreground: '#EDEDED',
        primary: {
          DEFAULT: '#00F0FF',
          hover: '#00C2CC',
          glow: 'rgba(0, 240, 255, 0.5)',
          foreground: '#050505',
        },
        secondary: {
          DEFAULT: '#7000FF',
          hover: '#5A00CC',
          glow: 'rgba(112, 0, 255, 0.5)',
          foreground: '#FFFFFF',
        },
        muted: {
          DEFAULT: '#12121A',
          foreground: '#A1A1AA',
        },
        accent: {
          DEFAULT: '#12121A',
          foreground: '#EDEDED',
        },
        card: {
          DEFAULT: '#0A0A0F',
          foreground: '#EDEDED',
        },
        popover: {
          DEFAULT: '#0A0A0F',
          foreground: '#EDEDED',
        },
        border: 'rgba(255, 255, 255, 0.08)',
        input: 'rgba(255, 255, 255, 0.08)',
        ring: '#00F0FF',
        destructive: {
          DEFAULT: '#FF0055',
          foreground: '#FFFFFF',
        },
        success: '#00FF94',
        warning: '#FFD600',
        info: '#00F0FF',
      },
      borderRadius: {
        lg: '8px',
        md: '4px',
        sm: '2px',
        xl: '12px',
      },
      boxShadow: {
        'neon': '0 0 20px -5px rgba(0, 240, 255, 0.5)',
        'neon-violet': '0 0 20px -5px rgba(112, 0, 255, 0.5)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.36)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' }
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' }
        },
        'pulse-neon': {
          '0%, 100%': { boxShadow: '0 0 20px -5px rgba(0, 240, 255, 0.5)' },
          '50%': { boxShadow: '0 0 30px -5px rgba(0, 240, 255, 0.8)' }
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'pulse-neon': 'pulse-neon 2s ease-in-out infinite',
      },
    }
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
