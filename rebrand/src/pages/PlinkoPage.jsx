import { useEffect } from 'react'

// Plinko's canonical, wallet-integrated implementation is the dedicated
// /plinko-mzizi/ blueprint (its own DB models, its own real wallet debits).
// This page only exists so a stale bookmark or direct link to /games/plinko
// doesn't strand a player — it forwards to the real one rather than running
// a second, un-linked live-money copy of the same game.
function PlinkoPage() {
    useEffect(() => {
        window.location.href = '/plinko-mzizi/'
    }, [])

    return null
}

export default PlinkoPage
