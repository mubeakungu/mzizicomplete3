import { useEffect } from 'react'
import CrashGame from '../components/CrashGame/CrashGame'
import { useWallet } from '../context/WalletContext'

function CrashPage() {
    const { setActiveGame } = useWallet()
    useEffect(() => { setActiveGame('jetx') }, [setActiveGame])

    return <CrashGame />
}

export default CrashPage
