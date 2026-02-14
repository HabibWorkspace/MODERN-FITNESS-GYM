/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // FitCore Enhanced Color Scheme - Bold & Modern
        'fitnix-black': '#0A0A0A',           // Pure deep black
        'fitnix-charcoal': '#1C1C1E',        // Rich charcoal
        'fitnix-dark-gray': '#2C2C2E',       // Dark gray for depth
        'fitnix-lime': '#B6FF00',            // Vibrant electric lime (brighter)
        'fitnix-lime-glow': '#D4FF33',       // Bright lime glow
        'fitnix-dark-lime': '#8BC34A',       // Deep lime for contrast
        'fitnix-off-white': '#F5F5F7',       // Clean off-white
        'fitnix-gray': '#8E8E93',            // Neutral gray
        
        // Accent colors for variety
        'fitnix-cyan': '#00E5FF',            // Electric cyan (brighter)
        'fitnix-purple': '#D946EF',          // Bold purple (brighter)
        'fitnix-orange': '#FF9500',          // Vibrant orange
        'fitnix-red': '#FF3B30',             // Bold red
        'fitnix-blue': '#0EA5E9',            // Sky blue
        'fitnix-pink': '#EC4899',            // Hot pink
        
        // Legacy colors for backward compatibility
        primary: '#B6FF00',
        secondary: '#8BC34A',
        danger: '#FF3B30',
        warning: '#FF9500',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'display': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      fontWeight: {
        'thin': 100,
        'extralight': 200,
        'light': 300,
        'normal': 400,
        'medium': 500,
        'semibold': 600,
        'bold': 700,
        'extrabold': 800,
        'black': 900,
      },
      boxShadow: {
        'fitnix': '0 2px 12px rgba(182, 255, 0, 0.08)',
        'fitnix-lg': '0 6px 24px rgba(182, 255, 0, 0.12)',
        'fitnix-xl': '0 10px 30px rgba(182, 255, 0, 0.15)',
        'fitnix-glow': '0 0 20px rgba(182, 255, 0, 0.2)',
        'fitnix-inner': 'inset 0 2px 8px rgba(0, 0, 0, 0.4)',
        'neon-lime': '0 0 20px rgba(182, 255, 0, 0.6), 0 0 40px rgba(182, 255, 0, 0.4), 0 0 60px rgba(182, 255, 0, 0.2)',
        'neon-cyan': '0 0 10px rgba(0, 229, 255, 0.3), 0 0 20px rgba(0, 229, 255, 0.15)',
        'neon-purple': '0 0 10px rgba(217, 70, 239, 0.3), 0 0 20px rgba(217, 70, 239, 0.15)',
        'neon-red': '0 0 20px rgba(255, 59, 48, 0.6), 0 0 40px rgba(255, 59, 48, 0.4), 0 0 60px rgba(255, 59, 48, 0.2)',
      },
      backgroundImage: {
        'gradient-lime': 'linear-gradient(135deg, #B6FF00 0%, #8BC34A 100%)',
        'gradient-dark': 'linear-gradient(135deg, #1C1C1E 0%, #0A0A0A 100%)',
        'gradient-glow': 'linear-gradient(135deg, #B6FF00 0%, #D4FF33 50%, #B6FF00 100%)',
        'gradient-cyan': 'linear-gradient(135deg, #00E5FF 0%, #0EA5E9 100%)',
        'gradient-purple': 'linear-gradient(135deg, #D946EF 0%, #A855F7 100%)',
        'gradient-orange': 'linear-gradient(135deg, #FF9500 0%, #F97316 100%)',
        'gradient-mesh': 'radial-gradient(at 40% 20%, rgba(182, 255, 0, 0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(0, 229, 255, 0.1) 0px, transparent 50%), radial-gradient(at 0% 50%, rgba(217, 70, 239, 0.1) 0px, transparent 50%)',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'bounce-slow': 'bounce 3s infinite',
        'spin-slow': 'spin 3s linear infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        glow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(182, 255, 0, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(182, 255, 0, 0.6)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}