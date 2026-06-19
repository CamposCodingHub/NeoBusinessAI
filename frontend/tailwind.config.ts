import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand Premium - Deep Space
        brand: {
          900: '#0a0a0f',
          800: '#12121a',
          700: '#1a1a2e',
          600: '#252542',
          500: '#3a3a5c',
          400: '#5a5a8a',
          300: '#7a7ab8',
          200: '#9a9ad8',
          100: '#babaf8',
          50: '#e0e0ff',
        },
        // Accent - Neon Glow
        accent: {
          cyan: '#00f5ff',
          'cyan-dark': '#00c8d0',
          purple: '#a855f7',
          'purple-dark': '#7c3aed',
          pink: '#ec4899',
          'pink-dark': '#be185d',
          blue: '#3b82f6',
          'blue-dark': '#1d4ed8',
        },
        // Surface - Glassmorphism
        surface: {
          dark: 'rgba(10, 10, 15, 0.8)',
          glass: 'rgba(255, 255, 255, 0.05)',
          'glass-hover': 'rgba(255, 255, 255, 0.1)',
          elevated: 'rgba(20, 20, 35, 0.9)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-mesh': 'linear-gradient(135deg, rgba(0,245,255,0.1) 0%, rgba(168,85,247,0.1) 50%, rgba(236,72,153,0.1) 100%)',
        'gradient-glow': 'radial-gradient(ellipse at center, rgba(0,245,255,0.2) 0%, transparent 70%)',
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
          '0%, 100%': { boxShadow: '0 0 20px rgba(0,245,255,0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(0,245,255,0.6)' },
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
        'neon-cyan': '0 0 20px rgba(0, 245, 255, 0.5), 0 0 40px rgba(0, 245, 255, 0.3)',
        'neon-purple': '0 0 20px rgba(168, 85, 247, 0.5), 0 0 40px rgba(168, 85, 247, 0.3)',
        'neon-pink': '0 0 20px rgba(236, 72, 153, 0.5), 0 0 40px rgba(236, 72, 153, 0.3)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'elevated': '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
      },
    },
  },
  plugins: [],
}

export default config
