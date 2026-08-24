import { lazy, Suspense, useEffect } from 'react'
import { useWallet } from '../context/WalletContext'

let phaserPromise

function loadPhaser() {
    if (window.Phaser) return Promise.resolve()

    phaserPromise ||= new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = `${import.meta.env.BASE_URL}vendor/phaser-arcade-physics.min.js`
        script.onload = () => window.Phaser ? resolve() : reject(new Error('Phaser failed to load'))
        script.onerror = () => reject(new Error('Phaser failed to load'))
        document.head.append(script)
    })

    return phaserPromise
}

const DinoGame = lazy(async () => {
    await loadPhaser()
    return import('../components/DinoGame')
})

function DinoPage() {
    const { setActiveGame } = useWallet()
    useEffect(() => { setActiveGame('dino') }, [setActiveGame])

    return <Suspense fallback={null}><DinoGame /></Suspense>
}

export default DinoPage
