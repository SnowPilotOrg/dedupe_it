const { nextui } = require('@nextui-org/react')

/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './index.html',
        './src/**/*.{js,ts,jsx,tsx}',
        './node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}',
    ],
    theme: {
        extend: {
            keyframes: {
                'glow-pulse': {
                    '0%, 100%': { boxShadow: '0 0 10px rgba(147,51,234,0.7)' },
                    '50%': { boxShadow: '0 0 15px rgba(147,51,234,0.9)' },
                },
            },
            animation: {
                'glow-pulse': 'glow-pulse 1.2s ease-out infinite',
            },
        },
    },
    darkMode: 'class',
    plugins: [nextui()],
}
