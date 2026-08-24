import { useEffect } from 'react'

// Mines' canonical, wallet-integrated implementation lives at
// /casino/play/mines (app/templates/games/mines.html, settling through the
// same /api/casino endpoints). This page only exists so a stale bookmark
// or direct link to /games/mines doesn't strand a player — it forwards to
// the real one rather than running a second, un-linked live-money copy.
function MinesPage() {
    useEffect(() => {
        window.location.href = '/casino/play/mines'
    }, [])

    return null
}

export default MinesPage
