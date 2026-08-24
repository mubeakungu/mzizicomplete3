export const GAMES = [
    { id: 'crash', name: 'Crash', navLabel: 'Crash', path: '/crash', icon: 'original', image: `${import.meta.env.BASE_URL}images/crash.avif`, rtp: '97% RTP', volatility: 'High volatility' },
    { id: 'plinko', name: 'Plinko', navLabel: 'Plinko', path: '/plinko', icon: 'plinko', image: `${import.meta.env.BASE_URL}images/plinko.avif`, rtp: '96% RTP', volatility: 'Medium volatility' },
    { id: 'dino', name: 'Dino', navLabel: 'Dino Run', path: '/dino', icon: 'dino', image: `${import.meta.env.BASE_URL}images/dino.avif`, rtp: '96% RTP', volatility: 'Low volatility' },
    { id: 'mines', name: 'Mines', navLabel: 'Mines', path: '/mines', icon: 'mines', image: `${import.meta.env.BASE_URL}images/mines.avif`, rtp: '96% RTP', volatility: 'Medium volatility' },
]

export function isGamePath(pathname) {
    return GAMES.some((game) => pathname.startsWith(game.path))
}
