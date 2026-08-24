import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'

const WalletContext = createContext(null)

const gameIdCache = {}

async function resolveGameId(slug) {
    if (gameIdCache[slug]) return gameIdCache[slug]
    const res = await fetch(`/api/casino/game-by-slug/${slug}`, { credentials: 'same-origin' })
    if (!res.ok) throw new Error(`Unknown game slug: ${slug}`)
    const data = await res.json()
    gameIdCache[slug] = data.id
    return data.id
}

export function WalletProvider({ children }) {
    const [balance, setBalance] = useState(0)
    const [loaded, setLoaded] = useState(false)
    const [currency, setCurrency] = useState('KES')
    const [transactions, setTransactions] = useState([])

    // Which catalog game is currently mounted, and the round currently in
    // flight for it (set by init-round, cleared by settle-round).
    const activeGameSlugRef = useRef(null)
    const activeRoundRef = useRef(null) // { round_id, game_id }

    const [toasts, setToasts] = useState([])
    const toastIdRef = useRef(0)

    const showToast = useCallback((type, title, description, duration = 3000) => {
        const id = ++toastIdRef.current
        setToasts(prev => [...prev, { id, type, title, description }])
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, duration)
    }, [])

    const refreshBalance = useCallback(async () => {
        try {
            const res = await fetch('/api/casino/get-balance', { credentials: 'same-origin' })
            if (res.ok) {
                const data = await res.json()
                setBalance(data.balance)
                if (data.currency) setCurrency(data.currency)
            }
        } catch (e) {
            // Network hiccup — keep showing the last known balance rather than zeroing it.
        } finally {
            setLoaded(true)
        }
    }, [])

    useEffect(() => {
        refreshBalance()
    }, [refreshBalance])

    // Called by each game page on mount so placeBet/addWinnings know which
    // catalog game_id to settle against.
    const setActiveGame = useCallback((slug) => {
        activeGameSlugRef.current = slug
        activeRoundRef.current = null
    }, [])

    // Kept synchronous so existing call sites (`if (!placeBet(amount))`)
    // don't need to change: does the balance check + optimistic deduction
    // immediately, then debits the real wallet via /api/casino/init-round
    // in the background and reconciles balance to the server's number once
    // that resolves. If the server call fails, the optimistic deduction is
    // rolled back and the player is told the bet didn't go through.
    const placeBet = useCallback((amount) => {
        const amt = parseFloat(amount)
        if (isNaN(amt) || amt <= 0 || amt > balance) return false

        const slug = activeGameSlugRef.current
        if (!slug) {
            console.error('placeBet called with no active game set (call setActiveGame first)')
            return false
        }

        setBalance(prev => parseFloat((prev - amt).toFixed(2)))
        setTransactions(txs => [
            { id: Date.now(), type: 'bet', amount: -amt, timestamp: new Date() },
            ...txs,
        ].slice(0, 100))

        ;(async () => {
            try {
                const gameId = await resolveGameId(slug)
                const res = await fetch('/api/casino/init-round', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({ game_id: gameId, stake: amt }),
                })
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}))
                    throw new Error(err.error || 'init-round failed')
                }
                const data = await res.json()
                activeRoundRef.current = { round_id: data.round_id, game_id: gameId }
                setBalance(data.balance) // reconcile to server truth
            } catch (e) {
                console.error('Bet failed to register with the server:', e)
                showToast('error', 'Bet not confirmed', 'Something went wrong reaching the server — your balance has been restored.')
                refreshBalance()
            }
        })()

        return true
    }, [balance, refreshBalance, showToast])

    // Same pattern: optimistic credit immediately, real settle-round call in
    // the background, reconciled to server balance once it resolves.
    const addWinnings = useCallback((amount) => {
        const amt = parseFloat(amount)
        if (isNaN(amt) || amt <= 0) return

        setBalance(prev => parseFloat((prev + amt).toFixed(2)))
        setTransactions(txs => [
            { id: Date.now(), type: 'win', amount: amt, timestamp: new Date() },
            ...txs,
        ].slice(0, 100))

        const round = activeRoundRef.current
        if (!round) {
            console.error('addWinnings called with no round in flight — nothing to settle server-side')
            return
        }
        activeRoundRef.current = null

        ;(async () => {
            try {
                const res = await fetch('/api/casino/settle-round', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({ round_id: round.round_id, game_id: round.game_id, payout: amt }),
                })
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}))
                    throw new Error(err.error || 'settle-round failed')
                }
                const data = await res.json()
                setBalance(data.balance) // reconcile to server truth
            } catch (e) {
                console.error('Payout failed to register with the server:', e)
                showToast('error', 'Payout not confirmed', 'Something went wrong reaching the server — refreshing your balance.')
                refreshBalance()
            }
        })()
    }, [refreshBalance, showToast])

    // A round that resolves as a loss (no payout) still needs to be marked
    // settled server-side so it doesn't sit "pending" forever in the audit
    // trail. The stake was already debited at placeBet time, so this call
    // moves no money — it just closes the round record.
    const settleLoss = useCallback(() => {
        const round = activeRoundRef.current
        if (!round) return
        activeRoundRef.current = null

        fetch('/api/casino/settle-round', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ round_id: round.round_id, game_id: round.game_id, payout: 0 }),
        }).catch(() => { /* best-effort close-out, not money-affecting */ })
    }, [])

    // Deposits/withdrawals go through the real wallet pages, not this panel.
    const deposit = useCallback(() => {
        showToast('info', 'Use your wallet', 'Deposit via M-Pesa from the Wallet page — real balance, not this demo panel.')
    }, [showToast])

    const resetBalance = useCallback(() => {
        refreshBalance()
    }, [refreshBalance])

    const value = {
        balance,
        loaded,
        currency,
        setCurrency,
        transactions,
        placeBet,
        addWinnings,
        settleLoss,
        deposit,
        resetBalance,
        updateBalance: refreshBalance,
        setActiveGame,
        toasts,
        showToast,
    }

    return (
        <WalletContext.Provider value={value}>
            {children}
        </WalletContext.Provider>
    )
}

export function useWallet() {
    const context = useContext(WalletContext)
    if (!context) {
        throw new Error('useWallet must be used within a WalletProvider')
    }
    return context
}

export default WalletContext
