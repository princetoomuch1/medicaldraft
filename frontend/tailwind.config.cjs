/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
        extend: {
            colors: {
                bg: 'var(--bg)',
                surface: 'var(--surface)',
                primary: 'var(--text-primary)',
                secondary: 'var(--text-secondary)',
                critical: 'var(--accent-critical)',
                signal: 'var(--signal-normal)',
                paper: 'var(--paper-bg)',
                ink: 'var(--ink)'
            },
            fontFamily: {
                heading: ['Space Grotesk', 'sans-serif'],
                editorial: ['Fraunces', 'serif'],
                mono: ['IBM Plex Mono', 'monospace'],
                ui: ['Plus Jakarta Sans', 'sans-serif']
            }
        }
    },
    plugins: []
};