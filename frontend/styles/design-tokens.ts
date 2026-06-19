/**
 * 🔥 DESIGN SYSTEM PREMIUM - NEOBUSINESS AI
 * Nível: Enterprise SaaS Global (Linear, Notion, Stripe, Vercel)
 */

// ============================================
// 🎨 CORES - PALETA PREMIUM
// ============================================
export const colors = {
  // Brand Principal
  brand: {
    navy: '#0A2540',         // Fundo escuro, headers premium
    navyLight: '#1A3A5C',    // Variação mais clara
    navyDark: '#051A2E',     // Variação mais escura
  },

  // Acentos Vibrantes
  accent: {
    coral: '#FF6B4A',        // Ação principal, CTAs
    coralLight: '#FF8F7A',   // Hover states
    coralDark: '#E55A3B',    // Active states
    teal: '#00D4AA',         // Sucesso, confirmação
    tealLight: '#4DDFC4',    // Hover sucesso
    gold: '#FFB800',         // Atenção, badges premium
    goldLight: '#FFD166',    // Hover atenção
    purple: '#9B37FF',       // Destaques especiais
    purpleLight: '#B56BFF',  // Hover premium
  },

  // Neutros Sofisticados
  neutral: {
    50: '#FAFBFC',           // Backgrounds claros
    100: '#F6F9FC',          // Cards, surfaces
    200: '#E3E8EE',          // Bordas sutis
    300: '#C9D2DC',          // Divisores
    400: '#9BA6B4',          // Texto terciário
    500: '#6B7280',          // Texto secundário
    600: '#4B5563',          // Labels
    700: '#374151',          // Texto body
    800: '#1F2937',          // Texto headings
    900: '#111827',          // Texto principal
    950: '#030712',          // Texto premium
  },

  // Estados Semânticos
  semantic: {
    success: '#00D4AA',
    warning: '#FFB800',
    error: '#FF4444',
    info: '#3B82F6',
  },

  // Dark Mode Premium
  dark: {
    bg: '#0A0F1A',           // Background principal
    surface: '#141B2A',       // Cards, modais
    elevated: '#1E2738',    // Hover, dropdowns
    border: '#2A3447',      // Bordas
    text: {
      primary: '#F8FAFC',
      secondary: '#94A3B8',
      tertiary: '#64748B',
    }
  }
};

// ============================================
// 🔤 TIPOGRAFIA - INTER + SF PRO
// ============================================
export const typography = {
  fontFamily: {
    sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace',
  },

  sizes: {
    xs: { size: '12px', lineHeight: '16px', letterSpacing: '0.02em' },
    sm: { size: '14px', lineHeight: '20px', letterSpacing: '0' },
    base: { size: '16px', lineHeight: '24px', letterSpacing: '0' },
    lg: { size: '18px', lineHeight: '28px', letterSpacing: '-0.01em' },
    xl: { size: '20px', lineHeight: '28px', letterSpacing: '-0.01em' },
    '2xl': { size: '24px', lineHeight: '32px', letterSpacing: '-0.02em' },
    '3xl': { size: '30px', lineHeight: '36px', letterSpacing: '-0.02em' },
    '4xl': { size: '36px', lineHeight: '40px', letterSpacing: '-0.02em' },
    '5xl': { size: '48px', lineHeight: '56px', letterSpacing: '-0.03em' },
    '6xl': { size: '60px', lineHeight: '64px', letterSpacing: '-0.03em' },
  },

  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // Estilos pré-definidos
  styles: {
    hero: {
      fontSize: '48px',
      lineHeight: '56px',
      fontWeight: 700,
      letterSpacing: '-0.03em',
    },
    h1: {
      fontSize: '36px',
      lineHeight: '44px',
      fontWeight: 600,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '30px',
      lineHeight: '36px',
      fontWeight: 600,
      letterSpacing: '-0.02em',
    },
    h3: {
      fontSize: '24px',
      lineHeight: '32px',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    body: {
      fontSize: '16px',
      lineHeight: '24px',
      fontWeight: 400,
    },
    bodySmall: {
      fontSize: '14px',
      lineHeight: '20px',
      fontWeight: 400,
    },
    caption: {
      fontSize: '12px',
      lineHeight: '16px',
      fontWeight: 500,
      letterSpacing: '0.05em',
      textTransform: 'uppercase',
    },
  }
};

// ============================================
// 📐 ESPAÇAMENTO - GRID SYSTEM
// ============================================
export const spacing = {
  // Escala de 4px base
  0: '0',
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
  16: '64px',
  20: '80px',
  24: '96px',
  32: '128px',

  // Nomeados
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
  '4xl': '96px',
};

// ============================================
// 🎯 BORDAS E RADIOS
// ============================================
export const borders = {
  radius: {
    none: '0',
    sm: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '24px',
    full: '9999px',
  },
  width: {
    thin: '1px',
    normal: '2px',
    thick: '4px',
  },
};

// ============================================
// ✨ SOMBRAS - ELEVATION SYSTEM
// ============================================
export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.04)',
  md: '0 4px 12px rgba(0, 0, 0, 0.05)',
  lg: '0 8px 24px rgba(0, 0, 0, 0.06)',
  xl: '0 16px 48px rgba(0, 0, 0, 0.08)',
  '2xl': '0 24px 64px rgba(0, 0, 0, 0.10)',

  // Sombras especiais
  glow: {
    coral: '0 0 40px rgba(255, 107, 74, 0.3)',
    teal: '0 0 40px rgba(0, 212, 170, 0.3)',
    purple: '0 0 40px rgba(155, 55, 255, 0.3)',
  },

  // Glassmorphism
  glass: '0 8px 32px rgba(0, 0, 0, 0.08), inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
};

// ============================================
// 🎬 ANIMAÇÕES - MICRO-INTERACTIONS
// ============================================
export const animations = {
  // Durações
  duration: {
    instant: '50ms',
    fast: '150ms',
    normal: '200ms',
    slow: '300ms',
    slower: '500ms',
  },

  // Easings premium
  easing: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    smooth: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
  },

  // Keyframes
  keyframes: {
    fadeIn: `
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    `,
    slideUp: `
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    `,
    pulse: `
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    `,
    shimmer: `
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    `,
    typing: `
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    `,
  },
};

// ============================================
// 🎛️ Z-INDEX SCALE
// ============================================
export const zIndex = {
  hide: -1,
  base: 0,
  dropdown: 100,
  sticky: 200,
  fixed: 300,
  modal: 400,
  popover: 500,
  tooltip: 600,
  toast: 700,
  highest: 9999,
};

// ============================================
// 📱 BREAKPOINTS
// ============================================
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// ============================================
// 🎨 GRADIENTES PREMIUM
// ============================================
export const gradients = {
  brand: 'linear-gradient(135deg, #0A2540 0%, #1A3A5C 100%)',
  accent: 'linear-gradient(135deg, #FF6B4A 0%, #FF8F7A 100%)',
  hero: 'linear-gradient(135deg, #0A2540 0%, #9B37FF 50%, #FF6B4A 100%)',
  glass: 'linear-gradient(180deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
  shimmer: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%)',
};

// ============================================
// 🔧 EXPORTS ÚTEIS
// ============================================
export const theme = {
  colors,
  typography,
  spacing,
  borders,
  shadows,
  animations,
  zIndex,
  breakpoints,
  gradients,
};

export default theme;
