import type { Config } from 'tailwindcss'

/**
 * Brand tokens: TRUST palette (navy / slate / teal).
 * Accent cyan/purple/pink keys remain as aliases so legacy classnames keep compiling,
 * but values are remapped away from neon “AI SaaS” purple/cyan glow.
 */
const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand — Trust Navy / Slate
        brand: {
          900: '#0C1B2A',
          800: '#0f172a',
          700: '#1e293b',
          600: '#334155',
          500: '#475569',
          400: '#64748b',
          300: '#94a3b8',
          200: '#cbd5e1',
          100: '#e2e8f0',
          50: '#f1f5f9',
        },
        // Accent — Teal credibility (+ softened aliases)
        accent: {
          teal: '#0F766E',
          'teal-soft': '#0d9488',
          'teal-deep': '#115e59',
          // aliases (legacy names → trust tones)
          cyan: '#0d9488',
          'cyan-dark': '#0F766E',
          purple: '#1e293b',
          'purple-dark': '#0f172a',
          pink: '#334155',
          'pink-dark': '#1e293b',
          blue: '#1e40af',
          'blue-dark': '#1e3a8a',
        },
        // Surface — calm professional panels
        surface: {
          dark: 'rgba(12, 27, 42, 0.92)',
          glass: 'rgba(255, 255, 255, 0.06)',
          'glass-hover': 'rgba(255, 255, 255, 0.1)',
          elevated: 'rgba(15, 23, 42, 0.94)',
        },
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-mesh':
          'linear-gradient(135deg, rgba(15,118,110,0.1) 0%, rgba(12,27,42,0.08) 50%, rgba(30,41,59,0.1) 100%)',
        'gradient-glow':
          'radial-gradient(ellipse at center, rgba(15,118,110,0.18) 0%, transparent 70%)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'typing': 'typing 1s ease-in-out infinite',
        'fade-in-up': 'fadeInUp 0.5s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'spin-slow': 'spin 8s linear infinite',
        'bounce-gentle': 'bounceGentle 2s ease-in-out infinite',
        'gradient-x': 'gradientX 15s ease infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 16px rgba(15,118,110,0.25)' },
          '50%': { boxShadow: '0 0 28px rgba(15,118,110,0.4)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'typing': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        },
        'fadeInUp': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'scaleIn': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'bounceGentle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        'gradientX': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'glowPulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'neon-cyan': '0 0 16px rgba(15, 118, 110, 0.35), 0 0 32px rgba(15, 118, 110, 0.18)',
        'neon-purple': '0 0 16px rgba(30, 41, 59, 0.35), 0 0 32px rgba(12, 27, 42, 0.2)',
        'neon-pink': '0 0 16px rgba(51, 65, 85, 0.3), 0 0 32px rgba(15, 23, 42, 0.18)',
        'glass': '0 8px 32px 0 rgba(12, 27, 42, 0.28)',
        'elevated': '0 25px 50px -12px rgba(12, 27, 42, 0.45)',
        'trust': '0 1px 0 rgba(15, 23, 42, 0.04), 0 8px 24px rgba(12, 27, 42, 0.06)',
      },
    },
  },
  plugins: [],
}

export default config
