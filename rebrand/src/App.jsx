import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { App as AntApp } from 'antd'

// This SPA is mounted at /games/* purely as the embedded implementation
// for individual catalog games (jetx→crash, dino) — it is NOT a second
// site. No Layout/Sidebar/Header/HomePage here: the real MziziBet chrome
// (nav, wallet button, casino lobby) is the one and only site shell.
// Each route below renders just that one game, full-bleed, with nothing
// else around it.
const CrashPage = lazy(() => import('./pages/CrashPage'))
const PlinkoPage = lazy(() => import('./pages/PlinkoPage'))
const DinoPage = lazy(() => import('./pages/DinoPage'))
const MinesPage = lazy(() => import('./pages/MinesPage'))

function App() {
    return (
        <AntApp>
            <Suspense
                fallback={
                    <div className="route-loading" role="status" aria-live="polite">
                        Loading…
                    </div>
                }
            >
                <Routes>
                    <Route path="/crash" element={<CrashPage />} />
                    <Route path="/plinko" element={<PlinkoPage />} />
                    <Route path="/dino" element={<DinoPage />} />
                    <Route path="/mines" element={<MinesPage />} />
                    {/* No standalone home/lobby here — send stragglers to the real one. */}
                    <Route path="*" element={<Navigate to="/crash" replace />} />
                </Routes>
            </Suspense>
        </AntApp>
    )
}

export default App
