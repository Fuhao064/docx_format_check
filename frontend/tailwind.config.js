/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        // 重新定义暗色模式色调为蓝灰色系
        zinc: {
          '950': 'var(--bg-primary)',
          '900': 'var(--bg-secondary)',
          '800': 'var(--bg-tertiary)',
          '700': '#3f3f46',
          '600': '#52525b',
          '500': '#71717a',
          '400': '#a1a1aa',
          '300': '#d4d4d8',
          '200': '#e4e4e7',
          '100': '#f4f4f5',
          '50': '#fafafa'
        },
        // 新增品牌色调
        brand: {
          DEFAULT: 'var(--brand-color)',
          light: 'var(--brand-color-light)',
          dark: 'var(--brand-color-dark)',
        },
        background: 'var(--bg-primary)',
        foreground: 'var(--text-primary)',
        border: 'var(--border-color)',
        input: 'var(--bg-tertiary)',
        ring: 'var(--accent-color)',
        primary: {
          DEFAULT: 'var(--accent-color)',
          foreground: 'var(--text-primary)'
        },
        secondary: {
          DEFAULT: 'var(--bg-tertiary)',
          foreground: 'var(--text-secondary)'
        },
        destructive: {
          DEFAULT: 'var(--error-color)',
          foreground: 'white'
        },
        success: {
          DEFAULT: 'var(--success-color)',
          foreground: 'white'
        },
        warning: {
          DEFAULT: 'var(--warning-color)',
          foreground: 'white'
        },
        info: {
          DEFAULT: 'var(--info-color)',
          foreground: 'white'
        }
      },
      borderRadius: {
        'sm': 'var(--border-radius-sm)',
        'md': 'var(--border-radius-md)',
        'lg': 'var(--border-radius-lg)'
      },
      transitionDuration: {
        DEFAULT: 'var(--transition-speed)'
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'slide-up': 'slideUp 0.3s ease-out forwards',
        'slide-down': 'slideDown 0.3s ease-out forwards',
        'progress': 'progress 5s linear forwards'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        progress: {
          '0%': { width: '100%' },
          '100%': { width: '0%' }
        }
      }
    }
  },
  plugins: []
}