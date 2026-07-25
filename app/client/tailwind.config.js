/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      fontSize: {
        '3xs': ['0.375rem', { lineHeight: '0.875rem' }],   // 6px  — tiny badges, indicators
        '2xs': ['0.5rem', { lineHeight: '0.75rem' }],      // 8px  — badges, labels, status
        'xs': ['0.75rem', { lineHeight: '1rem' }],          // 12px — body small, descriptions
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],      // 14px — body, cards
        'base': ['1rem', { lineHeight: '1.5rem' }],         // 16px — default
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],      // 18px — headings small
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],       // 20px — headings
        '2xl': ['1.5rem', { lineHeight: '2rem' }],          // 24px — section titles
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],     // 30px — stats
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],       // 36px — hero stats
        '5xl': ['3rem', { lineHeight: '1' }],               // 48px — large hero
      },
      colors: {
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        // Legacy aliases (for backward compatibility with existing code)
        bg: 'var(--background)',
        surface: 'var(--card)',
        surface2: 'var(--secondary)',
      },
      borderRadius: {
        none: "0",
        sm: "calc(var(--radius) - 4px)",
        DEFAULT: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        lg: "var(--radius)",
        xl: "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 8px)",
        full: "9999px",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
