import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
            phaser: path.resolve(__dirname, "./src/vendor/phaser-global.js"),
        },
    },
    optimizeDeps: {
        exclude: ['phaser'],
    },

    // Must match Flask's games_static url prefix
    base: '/games/',

    build: {
        // Outputs directly into Flask's static/games folder
        // Run: cd rebrand && npm install && npm run build
        outDir: '../app/static/games',
        emptyOutDir: true,
    },

    server: {
        port: 5173,
        proxy: {
            '/api':    'http://localhost:5000',
            '/auth':   'http://localhost:5000',
            '/wallet': 'http://localhost:5000',
        },
    },
})
