# Mobile UI/UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a usable, accessible mobile shell and game-first responsive layouts to the five existing routes without changing desktop behavior or game logic.

**Architecture:** Add two presentation primitives: `MobileNavigation` owns the five-route bottom navigation and Ant Design drawer, while `MobileBetSheet` wraps each existing betting panel with shared collapsed/expanded behavior. Route components keep their existing state and engines; route CSS controls ordering, compact content, canvas sizing, and mobile dialogs. Implement and browser-verify each route independently in the approved order.

**Tech Stack:** React 18, React Router 6, Ant Design 6, CSS media queries, native `matchMedia`, Node `node:test`, Chrome DevTools Protocol.

## Global Constraints

- Cover only `/`, `/mines`, `/crash`, `/dino`, and `/plinko`.
- Implement in this order: shared shell → Home → Mines → Crash → Dino → Plinko.
- Keep desktop behavior above `768px` unchanged.
- Support phone widths from `320px`, tablet widths through `1024px`, and representative landscape viewports.
- Use existing React, CSS, and Ant Design APIs; add no dependency.
- Preserve the exact Plinko implementation present when execution starts; snapshot all Plinko paths before editing presentation files.
- Do not modify `dist`.
- Run production builds only with an external `--outDir` outside the repository.
- Do not change game engines, fairness, wallet accounting, payouts, timing, Auto Bet semantics, or Plinko capacity behavior.
- Do not commit or push unless the user explicitly requests it.
- Use `node:test` source contracts before each production change, then verify the actual UI in Chrome.

## File Structure

**Create:**

- `src/components/MobileNavigation.jsx` — mobile drawer and five-route bottom navigation.
- `src/components/MobileNavigation.css` — mobile-only drawer/bottom-nav presentation and safe-area handling.
- `src/components/MobileBetSheet.jsx` — reusable collapsed/expanded betting-sheet behavior, keyboard handling, focus containment, and body scroll lock.
- `src/components/MobileBetSheet.css` — shared fixed-sheet presentation below `768px`; transparent wrapper above it.
- `mobile-ui.test.mjs` — dependency-free source/CSS regression contracts for all mobile stages.
- `scripts/verifyMobileUi.mjs` — dependency-free CDP smoke test for routes and target viewports.

**Modify:**

- `src/App.jsx` — replace the blank lazy-route fallback with a visible status.
- `src/components/Layout.jsx` — own drawer state and render mobile navigation.
- `src/components/Header.jsx` — reuse the current wallet state/dropdown through a compact mobile trigger and expose the menu trigger.
- `src/styles/index.css` — responsive application shell, viewport sizing, header, wallet panel, loading state, and overlay rules.
- `src/styles/home.css` — compact hero, horizontal categories, and one/two-column card grid.
- `src/components/MinesGame/MinesGame.jsx` — wrap the existing sidebar in `MobileBetSheet` and mark secondary controls.
- `src/components/MinesGame/MinesGame.css` — board-first mobile layout and compact/full sheet states.
- `src/components/CrashGame/CrashGame.jsx` — wrap the betting sidebar and add mobile player-data tabs without changing round logic.
- `src/components/CrashGame/BettingPanel.jsx` — mark secondary controls for collapsed sheet presentation.
- `src/components/CrashGame/CrashGame.css` — chart-first mobile layout, tabs, and dialogs.
- `src/components/DinoGame/DinoGame.jsx` — wrap the existing sidebar and collapse it while the game runs.
- `src/components/DinoGame/DinoGame.css` — game-first Phaser sizing, stable action controls, and landscape rules.
- `src/components/PlinkoGame/PlinkoGame.jsx` — wrap only the current sidebar and append mobile dialog classes to existing portal classes.
- `src/components/PlinkoGame/Sidebar.jsx` — mark controls that hide in collapsed mode.
- `src/components/PlinkoGame/PlinkoGame.css` — board-first route layout, recent-play scroller, dialogs.
- `src/components/PlinkoGame/Sidebar.css` — compact/expanded control visibility and horizontal ball cards.
- `src/components/PlinkoGame/Plinko.css` — preserve the current `760:570` board ratio and canvas alignment. The execution-start implementation has one `.plinko-canvas`; mobile work must not create a second canvas or refactor the engine.

**Must not change:**

- `src/context/WalletContext.jsx`
- `src/utils/ProvablyFair.js`
- `src/components/PlinkoGame/PlinkoEngine.js`
- `src/components/PlinkoGame/Ball.js`
- `src/components/PlinkoGame/dropPlinkoBall.js`
- `src/components/DinoGame/core/**`
- `public/plinko-outcomes.json`
- `scripts/generatePlinkoOutcomes.cjs`
- `dist/**`

Before Task 1, expand this protected list with every additional engine, fairness, generated asset, or Plinko regression path found under `src/components/PlinkoGame`, `public`, `scripts`, and the repository root. Later tasks may edit only the five Plinko presentation files explicitly listed above.

---

### Task 1: Establish the mobile regression harness and safety snapshot

**Files:**
- Create: `mobile-ui.test.mjs`
- Inspect only: `dist/**`

**Interfaces:**
- Consumes: current source files as UTF-8 text.
- Produces: `source(relativePath)` helper and staged `node:test` contracts used by every later task.

- [ ] **Step 1: Capture protected baselines outside the repository**

Run:

```bash
BASELINE_DIR="${TMPDIR:-/tmp}/stake-mobile-baseline"
ls "${TMPDIR:-/tmp}"
mkdir -p "$BASELINE_DIR"
git status --short > "$BASELINE_DIR/status-before.txt"
git status --short -- dist > "$BASELINE_DIR/dist-status-before.txt"
git diff --binary -- dist > "$BASELINE_DIR/dist-diff-before.patch"
git status --short -- src/components/PlinkoGame public scripts '*plinko*.test.mjs' > "$BASELINE_DIR/plinko-status-before.txt"
git diff --binary -- src/components/PlinkoGame public scripts '*plinko*.test.mjs' > "$BASELINE_DIR/plinko-diff-before.patch"
git status --short -- src/context/WalletContext.jsx src/utils/ProvablyFair.js src/components/PlinkoGame/PlinkoEngine.js src/components/PlinkoGame/Ball.js src/components/PlinkoGame/dropPlinkoBall.js src/components/DinoGame/core public/plinko-outcomes.json scripts/generatePlinkoOutcomes.cjs > "$BASELINE_DIR/protected-status-before.txt"
git diff --binary -- src/context/WalletContext.jsx src/utils/ProvablyFair.js src/components/PlinkoGame/PlinkoEngine.js src/components/PlinkoGame/Ball.js src/components/PlinkoGame/dropPlinkoBall.js src/components/DinoGame/core public/plinko-outcomes.json scripts/generatePlinkoOutcomes.cjs > "$BASELINE_DIR/protected-diff-before.patch"
```

Expected: every command succeeds and only files under the external temporary directory are created. Keep this shell open or rerun later commands with the same `BASELINE_DIR` value.

- [ ] **Step 2: Create the shared test helper and first failing shell contracts**

Create `mobile-ui.test.mjs` with:

```js
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

async function source(relativePath) {
    return readFile(new URL(relativePath, import.meta.url), 'utf8').catch(() => '')
}

async function sources(relativePaths) {
    return Promise.all(relativePaths.map(source))
}

test('mobile shell exposes drawer, compact header, and five-route bottom navigation', async () => {
    const [app, layout, header, navigation, navigationCss, globalCss] = await sources([
        './src/App.jsx',
        './src/components/Layout.jsx',
        './src/components/Header.jsx',
        './src/components/MobileNavigation.jsx',
        './src/components/MobileNavigation.css',
        './src/styles/index.css',
    ])

    assert.match(app, /role="status"/)
    assert.doesNotMatch(app, /fallback=\{null\}/)
    assert.match(layout, /<MobileNavigation/)
    assert.match(header, /aria-label="Open navigation menu"/)
    assert.match(header, /ref=\{menuButtonRef\}/)
    assert.match(navigation, /afterOpenChange=/)
    assert.match(header, /className="mobile-wallet-balance"/)
    assert.match(header, /aria-expanded=\{showWalletDropdown\}/)
    assert.match(header, /setShowWalletDropdown\(!showWalletDropdown\)/)
    assert.match(header, /!isGamePage &&/)
    assert.equal((header.match(/className="wallet-dropdown"/g) || []).length, 1)
    assert.match(navigation, /aria-label="Primary navigation"/)
    assert.match(navigation, /const primaryRoutes = \[/)
    assert.match(navigation, /path: '\/'/)
    assert.match(navigation, /\.\.\.GAMES\.map/)
    assert.match(navigation, /Coming soon/)
    assert.match(navigationCss, /safe-area-inset-bottom/)
    assert.match(globalCss, /height:\s*100dvh/)
    assert.match(globalCss, /padding-bottom:\s*var\(--mobile-nav-space\)/)
})

test('mobile bet sheet owns collapse, escape, focus, and scroll-lock behavior', async () => {
    const [component, css] = await sources([
        './src/components/MobileBetSheet.jsx',
        './src/components/MobileBetSheet.css',
    ])

    assert.match(component, /data-state=/)
    assert.match(component, /aria-expanded=/)
    assert.match(component, /event\.key === 'Escape'/)
    assert.match(component, /event\.key === 'Tab'/)
    assert.match(component, /backgroundNode\.inert = true/)
    assert.match(component, /aria-modal=/)
    assert.match(component, /mobile-overlay-open/)
    assert.match(css, /position:\s*fixed/)
    assert.match(css, /bottom:\s*var\(--mobile-nav-space\)/)
    assert.match(css, /prefers-reduced-motion/)
})
```

- [ ] **Step 3: Run the shell contracts and verify RED**

Run:

```bash
node --test mobile-ui.test.mjs
```

Expected: FAIL because `MobileNavigation.jsx` and `MobileBetSheet.jsx` do not exist and the current shell lacks the asserted hooks.

- [ ] **Step 4: Checkpoint without committing**

Run:

```bash
git status --short -- mobile-ui.test.mjs dist
```

Expected: only `mobile-ui.test.mjs` is new for this task; compare the current protected status against `$BASELINE_DIR/dist-status-before.txt` and `$BASELINE_DIR/plinko-status-before.txt` before continuing.

---

### Task 2: Build the shared mobile betting sheet

**Files:**
- Create: `src/components/MobileBetSheet.jsx`
- Create: `src/components/MobileBetSheet.css`
- Test: `mobile-ui.test.mjs`

**Interfaces:**
- Consumes props: `title: string`, `children: ReactNode`, `className?: string`, `collapseOn?: boolean`.
- Produces: `<MobileBetSheet>` with `data-state="collapsed|expanded"`; route CSS may hide `.mobile-sheet-secondary` while collapsed.

- [ ] **Step 1: Run only the missing-sheet contract and verify RED**

Run:

```bash
node --test --test-name-pattern="mobile bet sheet" mobile-ui.test.mjs
```

Expected: FAIL because the component and CSS are absent.

- [ ] **Step 2: Implement the minimum shared behavior**

Create `src/components/MobileBetSheet.jsx`:

```jsx
import { useEffect, useId, useRef, useState } from 'react'
import './MobileBetSheet.css'

const MOBILE_QUERY = '(max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none)'
const FOCUSABLE = 'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'

function MobileBetSheet({ title, children, className = '', collapseOn = false }) {
    const [expanded, setExpanded] = useState(false)
    const [isMobile, setIsMobile] = useState(() =>
        typeof window !== 'undefined' && window.matchMedia(MOBILE_QUERY).matches,
    )
    const contentId = useId()
    const sheetRef = useRef(null)

    useEffect(() => {
        const media = window.matchMedia(MOBILE_QUERY)
        const update = () => {
            setIsMobile(media.matches)
            if (!media.matches) setExpanded(false)
        }
        media.addEventListener('change', update)
        return () => media.removeEventListener('change', update)
    }, [])

    useEffect(() => {
        if (collapseOn) setExpanded(false)
    }, [collapseOn])

    useEffect(() => {
        if (!isMobile || !expanded) return
        const previousFocus = document.activeElement
        const sheet = sheetRef.current
        const backgroundNodes = []
        let activeBranch = sheet
        while (activeBranch?.parentElement && activeBranch.parentElement !== document.body) {
            for (const sibling of activeBranch.parentElement.children) {
                if (sibling !== activeBranch && !sibling.contains(activeBranch)) {
                    backgroundNodes.push(sibling)
                }
            }
            activeBranch = activeBranch.parentElement
        }
        const onKeyDown = (event) => {
            if (event.key === 'Escape') {
                setExpanded(false)
                return
            }
            if (event.key !== 'Tab') return
            const focusable = [...sheet.querySelectorAll(FOCUSABLE)]
            if (!focusable.length) return
            const first = focusable[0]
            const last = focusable.at(-1)
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault()
                last.focus()
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault()
                first.focus()
            }
        }

        for (const backgroundNode of backgroundNodes) backgroundNode.inert = true
        document.body.classList.add('mobile-overlay-open')
        document.addEventListener('keydown', onKeyDown)
        sheet.querySelector(FOCUSABLE)?.focus()
        return () => {
            for (const backgroundNode of backgroundNodes) backgroundNode.inert = false
            document.body.classList.remove('mobile-overlay-open')
            document.removeEventListener('keydown', onKeyDown)
            previousFocus?.focus()
        }
    }, [expanded, isMobile])

    return (
        <section
            ref={sheetRef}
            className={`mobile-bet-sheet ${className}`.trim()}
            data-state={expanded ? 'expanded' : 'collapsed'}
            role={expanded ? 'dialog' : undefined}
            aria-modal={expanded || undefined}
            aria-label={title}
        >
            <button
                type="button"
                className="mobile-bet-sheet__backdrop"
                aria-label="Collapse bet controls"
                onClick={() => setExpanded(false)}
            />
            <button
                type="button"
                className="mobile-bet-sheet__handle"
                aria-expanded={expanded}
                aria-controls={contentId}
                onClick={() => setExpanded(value => !value)}
            >
                <span>{title}</span>
                <span aria-hidden="true">{expanded ? '⌄' : '⌃'}</span>
            </button>
            <div id={contentId} className="mobile-bet-sheet__content">
                {children}
            </div>
        </section>
    )
}

export default MobileBetSheet
```

Create `src/components/MobileBetSheet.css`:

```css
.mobile-bet-sheet {
    display: contents;
}

.mobile-bet-sheet__handle,
.mobile-bet-sheet__backdrop {
    display: none;
}

@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .mobile-bet-sheet {
        --mobile-sheet-collapsed-height: 196px;
        position: fixed;
        z-index: 320;
        right: 0;
        bottom: var(--mobile-nav-space);
        left: 0;
        display: flex;
        max-height: calc(100dvh - var(--mobile-header-height) - var(--mobile-nav-space));
        flex-direction: column;
        border-top: 1px solid var(--border-default);
        border-radius: 16px 16px 0 0;
        background: var(--bg-sidebar);
        box-shadow: 0 -14px 40px rgba(0, 8, 20, 0.36);
        transition: max-height var(--transition-normal), transform var(--transition-normal);
    }

    .mobile-bet-sheet[data-state='collapsed'] {
        max-height: var(--mobile-sheet-collapsed-height);
    }

    .mobile-bet-sheet[data-state='expanded'] {
        max-height: min(72dvh, 680px);
    }

    .mobile-bet-sheet__backdrop {
        position: fixed;
        z-index: -1;
        inset: 0 0 var(--mobile-nav-space);
        border: 0;
        background: rgba(0, 8, 20, 0.58);
    }

    .mobile-bet-sheet[data-state='expanded'] .mobile-bet-sheet__backdrop {
        display: block;
    }

    .mobile-bet-sheet__handle {
        display: flex;
        min-height: 44px;
        align-items: center;
        justify-content: space-between;
        padding: 0 16px;
        border: 0;
        border-bottom: 1px solid var(--border-subtle);
        background: transparent;
        color: var(--text-primary);
        font: inherit;
        font-weight: 800;
    }

    .mobile-bet-sheet__content {
        min-height: 0;
        overflow: auto;
        overscroll-behavior: contain;
    }

    .mobile-bet-sheet[data-state='collapsed'] .mobile-sheet-secondary {
        display: none !important;
    }

    body.mobile-overlay-open,
    body.mobile-overlay-open .main-content {
        overflow: hidden;
    }
}

@media (prefers-reduced-motion: reduce) {
    .mobile-bet-sheet {
        transition: none;
    }
}
```

- [ ] **Step 3: Run the sheet contract and verify GREEN**

Run:

```bash
node --test --test-name-pattern="mobile bet sheet" mobile-ui.test.mjs
```

Expected: PASS.

- [ ] **Step 4: Verify formatting**

Run:

```bash
git -c core.whitespace=cr-at-eol diff --check -- src/components/MobileBetSheet.jsx src/components/MobileBetSheet.css mobile-ui.test.mjs
```

Expected: no output.

---

### Task 3: Implement the shared mobile header, drawer, bottom navigation, and route loading state

**Files:**
- Create: `src/components/MobileNavigation.jsx`
- Create: `src/components/MobileNavigation.css`
- Modify: `src/App.jsx`
- Modify: `src/components/Layout.jsx`
- Modify: `src/components/Header.jsx`
- Modify: `src/styles/index.css`
- Test: `mobile-ui.test.mjs`

**Interfaces:**
- Consumes: `GAMES`, `useThemeSettings`, current route, existing `showWalletDropdown` state, `drawerOpen/onClose` props, and a shared menu-button ref.
- Produces: `MobileNavigation({ drawerOpen, onClose, returnFocusRef })`; `Header({ menuOpen, menuButtonRef, onMenuClick })`; one shared desktop/mobile wallet dropdown; explicit drawer focus restoration; visible lazy-route status; CSS variables `--mobile-header-height`, `--mobile-nav-height`, and `--mobile-nav-space`.

- [ ] **Step 1: Run the shell contract and verify RED**

Run:

```bash
node --test --test-name-pattern="mobile shell" mobile-ui.test.mjs
```

Expected: FAIL because navigation and shell hooks are absent.

- [ ] **Step 2: Add mobile navigation using existing Ant Drawer**

Create `src/components/MobileNavigation.jsx`:

```jsx
import { useEffect } from 'react'
import { Drawer } from 'antd'
import { NavLink, useLocation } from 'react-router-dom'
import { GAMES } from '../games'
import { useThemeSettings } from '../context/ThemeContext'
import './MobileNavigation.css'

const primaryRoutes = [
    { path: '/', label: 'Home', icon: '⌂' },
    ...GAMES.map(game => ({ path: game.path, label: game.name, icon: '◆' })),
]

const comingSoon = ['Favourites', 'Recent', 'Challenges', 'My Bets']

function MobileNavigation({ drawerOpen, onClose, returnFocusRef }) {
    const location = useLocation()
    const { paletteId, palettes, setPaletteId } = useThemeSettings()

    useEffect(() => onClose(), [location.pathname, onClose])

    return (
        <>
            <Drawer
                title="Menu"
                placement="left"
                width="min(88vw, 360px)"
                open={drawerOpen}
                onClose={onClose}
                afterOpenChange={open => {
                    if (!open) returnFocusRef.current?.focus()
                }}
                rootClassName="mobile-navigation-drawer"
            >
                <label className="mobile-drawer-field">
                    <span>Search</span>
                    <input type="search" placeholder="Search your game" />
                </label>
                <label className="mobile-drawer-field">
                    <span>Palette</span>
                    <select value={paletteId} onChange={event => setPaletteId(event.target.value)}>
                        {palettes.map(palette => (
                            <option key={palette.id} value={palette.id}>{palette.name}</option>
                        ))}
                    </select>
                </label>
                <div className="mobile-drawer-actions" aria-label="Account shortcuts">
                    {['Profile', 'Notifications', 'Chat'].map(label => (
                        <button key={label} type="button">{label}</button>
                    ))}
                </div>
                <div className="mobile-coming-soon" aria-label="Coming soon">
                    {comingSoon.map(label => (
                        <button key={label} type="button" disabled>
                            <span>{label}</span>
                            <small>Coming soon</small>
                        </button>
                    ))}
                </div>
            </Drawer>

            <nav className="mobile-bottom-nav" aria-label="Primary navigation">
                {primaryRoutes.map(route => (
                    <NavLink
                        key={route.path}
                        to={route.path}
                        end={route.path === '/'}
                        className={({ isActive }) => isActive ? 'active' : ''}
                    >
                        <span aria-hidden="true">{route.icon}</span>
                        <span>{route.label}</span>
                    </NavLink>
                ))}
            </nav>
        </>
    )
}

export default MobileNavigation
```

Create `src/components/MobileNavigation.css`:

```css
.mobile-bottom-nav {
    display: none;
}

@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .mobile-bottom-nav {
        position: fixed;
        z-index: 350;
        right: 0;
        bottom: 0;
        left: 0;
        display: grid;
        height: var(--mobile-nav-space);
        grid-template-columns: repeat(5, minmax(0, 1fr));
        padding: 4px 4px env(safe-area-inset-bottom);
        border-top: 1px solid var(--border-subtle);
        background: var(--bg-header);
    }

    .mobile-bottom-nav a {
        display: flex;
        min-width: 44px;
        min-height: 44px;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 1px;
        border-radius: 8px;
        color: var(--text-secondary);
        font-size: 10px;
        font-weight: 700;
        text-decoration: none;
    }

    .mobile-bottom-nav a.active {
        background: var(--primary-soft);
        color: var(--primary-hover);
    }

    .mobile-navigation-drawer .ant-drawer-content {
        background: var(--bg-sidebar);
    }

    .mobile-drawer-field,
    .mobile-coming-soon,
    .mobile-drawer-actions {
        display: grid;
        gap: 8px;
        margin-bottom: 20px;
    }

    .mobile-drawer-field input,
    .mobile-drawer-field select,
    .mobile-drawer-actions button,
    .mobile-coming-soon button {
        min-height: 44px;
        border: 1px solid var(--border-default);
        border-radius: 8px;
        background: var(--surface-1);
        color: var(--text-primary);
        font: inherit;
    }

    .mobile-coming-soon button {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 12px;
        color: var(--text-disabled);
    }
}
```

- [ ] **Step 3: Wire drawer state through the shared shell**

Replace `src/components/Layout.jsx` with:

```jsx
import { useCallback, useRef, useState } from 'react'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import MobileNavigation from './MobileNavigation'

function Layout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true)
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
    const mobileMenuButtonRef = useRef(null)
    const closeMobileMenu = useCallback(() => setIsMobileMenuOpen(false), [])

    return (
        <div className="app-layout">
            <Sidebar
                isOpen={isSidebarOpen}
                toggleSidebar={() => setIsSidebarOpen(value => !value)}
            />
            <div className="app-main-wrapper">
                <Header
                    menuOpen={isMobileMenuOpen}
                    menuButtonRef={mobileMenuButtonRef}
                    onMenuClick={() => setIsMobileMenuOpen(true)}
                />
                <main className="main-content">
                    <Outlet />
                </main>
            </div>
            <MobileNavigation
                drawerOpen={isMobileMenuOpen}
                onClose={closeMobileMenu}
                returnFocusRef={mobileMenuButtonRef}
            />
        </div>
    )
}

export default Layout
```

In `src/App.jsx`, replace the blank Suspense fallback with:

```jsx
<Suspense
    fallback={
        <div className="route-loading" role="status" aria-live="polite">
            Loading…
        </div>
    }
>
```

In `src/components/Header.jsx`, change the signature to:

```jsx
function Header({ menuOpen, menuButtonRef, onMenuClick }) {
```

In `.header-center`, remove the outer `isGamePage ? wallet : search` ternary so `.header-wallet` is always rendered. Keep exactly one copy of its existing dropdown and add this compact trigger as its first child:

```jsx
<button
    type="button"
    className="mobile-wallet-balance"
    aria-label={`Open wallet, balance ${formattedBalance}`}
    aria-expanded={showWalletDropdown}
    onClick={() => setShowWalletDropdown(!showWalletDropdown)}
>
    <BtcIcon size={18} fontSize={11} />
    <span>{formattedBalance}</span>
</button>
```

Wrap only the existing `.wallet-balance-display`, `.wallet-btn`, and `.wallet-toast-container` blocks in `isGamePage && (...)`; leave `{showWalletDropdown && <div className="wallet-dropdown" ...>}` inside the shared `.header-wallet` without duplicating it. Render the existing `.search-input-wrapper` after `.header-wallet` under `!isGamePage && (...)`. This keeps desktop Home search unchanged while making the same wallet state and panel reachable from every mobile route.

Add this as the final child of `.header-right`:

```jsx
<button
    ref={menuButtonRef}
    type="button"
    className="mobile-menu-button"
    aria-label="Open navigation menu"
    aria-haspopup="dialog"
    aria-expanded={menuOpen}
    onClick={onMenuClick}
>
    <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
        <path d="M3 6h18v2H3V6m0 5h18v2H3v-2m0 5h18v2H3v-2z" />
    </svg>
</button>
```

- [ ] **Step 4: Add exact shared viewport/mobile CSS**

Add to `:root` in `src/styles/index.css`:

```css
--mobile-header-height: 52px;
--mobile-nav-height: 56px;
--mobile-nav-space: calc(var(--mobile-nav-height) + env(safe-area-inset-bottom));
```

Add the static/dynamic viewport fallback to `.app-layout`:

```css
height: 100vh;
height: 100dvh;
```

Add these defaults before responsive rules:

```css
.mobile-wallet-balance,
.mobile-menu-button {
    display: none;
}

.route-loading {
    display: grid;
    min-height: 100vh;
    min-height: 100dvh;
    place-items: center;
    background: var(--bg-primary);
    color: var(--text-primary);
}
```

Replace the existing `@media (max-width: 768px)` block with `@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none)`, retaining its `.app-sidebar`, game container, betting panel, and multiplier rules, then add:

```css
.header {
    height: var(--mobile-header-height);
    padding: env(safe-area-inset-top) 10px 0;
}

.header-center {
    min-width: 0;
    margin: 0 4px 0 auto;
}

.header-center .search-input-wrapper,
.header-right > :not(.mobile-menu-button),
.wallet-balance-display,
.wallet-btn {
    display: none;
}

.mobile-wallet-balance,
.mobile-menu-button {
    display: flex;
    min-height: 44px;
    align-items: center;
    justify-content: center;
}

.mobile-wallet-balance {
    max-width: min(44vw, 180px);
    gap: 6px;
    overflow: hidden;
    border: 0;
    background: transparent;
    color: var(--text-primary);
    font-weight: 800;
    white-space: nowrap;
}

.mobile-wallet-balance span {
    overflow: hidden;
    text-overflow: ellipsis;
}

.mobile-menu-button {
    min-width: 44px;
    border: 0;
    background: transparent;
    color: var(--text-primary);
}

.header-wallet .wallet-dropdown {
    position: fixed;
    top: calc(var(--mobile-header-height) + env(safe-area-inset-top) + 4px);
    right: 12px;
    left: 12px;
    width: auto;
    max-height: calc(100dvh - var(--mobile-header-height) - var(--mobile-nav-space) - 20px);
    overflow-y: auto;
    transform: none;
}

.main-content {
    padding-bottom: var(--mobile-nav-space);
    overflow-x: hidden;
    overflow-y: auto;
}
```

Inside the reduced-motion block, disable `.wallet-dropdown` animation on mobile so its fixed positioning does not inherit the desktop `translateX(-50%)` keyframes.

- [ ] **Step 5: Run shell tests and existing router/config regressions**

Run:

```bash
node --test --test-name-pattern="mobile shell" mobile-ui.test.mjs
node --test vite.config.test.mjs src/components/sidebar.test.mjs
```

Expected: all selected tests pass.

- [ ] **Step 6: Browser-check the shell before route work**

Start Vite on a dedicated port and Chrome with a clean profile:

```bash
npm run dev -- --host 127.0.0.1 --port 5210 --strictPort
CHROME_PROFILE="${TMPDIR:-/tmp}/stake-mobile-shell"
ls "${TMPDIR:-/tmp}"
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --remote-debugging-port=9340 --user-data-dir="$CHROME_PROFILE" --no-first-run --no-default-browser-check http://127.0.0.1:5210/
```

At `390×844`, verify on `/` and one game route: compact wallet opens the same deposit/history panel on both routes and the panel stays inside the viewport; five bottom links render; drawer opens from the menu button; all four missing routes show disabled “Coming soon”; `Escape` closes the drawer and restores menu-button focus; changing palette in the drawer updates the page; no horizontal scroll. At `1280×800`, verify Home search and the game wallet controls remain unchanged.

---

### Task 4: Make Home mobile-first

**Files:**
- Modify: `src/styles/home.css`
- Test: `mobile-ui.test.mjs`

**Interfaces:**
- Consumes: existing `.home-page-*`, `.game-category-*`, `.stake-games-grid`, and `.stake-card` markup.
- Produces: compact hero, horizontal category rail, two-column cards, and one-column cards below `360px`.

- [ ] **Step 1: Add a failing Home CSS contract**

Append to `mobile-ui.test.mjs`:

```js
test('Home uses compact mobile hero, category rail, and adaptive card grid', async () => {
    const css = await source('./src/styles/home.css')
    assert.match(css, /\.game-category-list\s*\{[^}]*overflow-x:\s*auto/s)
    assert.match(css, /@media\s*\(max-width:\s*640px\)[\s\S]*grid-template-columns:\s*repeat\(2,/)
    assert.match(css, /@media\s*\(max-width:\s*359px\)[\s\S]*grid-template-columns:\s*1fr/)
    assert.match(css, /touch-action:\s*pan-x/)
})
```

- [ ] **Step 2: Run the Home contract and verify RED**

Run:

```bash
node --test --test-name-pattern="Home uses" mobile-ui.test.mjs
```

Expected: FAIL because the category rail and narrow one-column breakpoint are absent.

- [ ] **Step 3: Extend `src/styles/home.css` minimally**

Add:

```css
.game-category-list {
    overflow-x: auto;
    overscroll-behavior-inline: contain;
    scrollbar-width: none;
    touch-action: pan-x;
}

.game-category-list::-webkit-scrollbar {
    display: none;
}

@media (max-width: 640px) {
    .home-page-container {
        padding-bottom: 12px;
    }

    .home-page-hero {
        padding-inline: 16px;
    }

    .hero-copy {
        padding-block: 24px;
    }

    .hero-title {
        font-size: clamp(34px, 10vw, 44px);
    }

    .game-category-nav,
    .home-section {
        padding-inline: 16px;
    }

    .game-category-list {
        flex-wrap: nowrap;
    }

    .game-category-chip {
        min-height: 44px;
        flex: 0 0 auto;
    }

    .stake-games-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 359px) {
    .stake-games-grid {
        grid-template-columns: 1fr;
    }
}
```

- [ ] **Step 4: Verify Home GREEN and browser behavior**

Run:

```bash
node --test --test-name-pattern="Home uses" mobile-ui.test.mjs
```

Expected: PASS.

Browser-check `/` at `320×568`, `375×667`, and `430×932`: no horizontal page scroll; category chips scroll horizontally; cards are one column at `320px` and two columns at `375px`/`430px`; final card clears bottom navigation; desktop remains unchanged.

---

### Task 5: Convert Mines to board-first mobile layout

**Files:**
- Modify: `src/components/MinesGame/MinesGame.jsx`
- Modify: `src/components/MinesGame/MinesGame.css`
- Test: `mobile-ui.test.mjs`

**Interfaces:**
- Consumes: `MobileBetSheet`, current Mines sidebar controls, grid, and existing modals.
- Produces: `.mines-bet-sheet`; `.mobile-sheet-secondary` markers; square board above the sheet; near-full-screen mobile dialogs.

- [ ] **Step 1: Add the failing Mines contract**

Append:

```js
test('Mines keeps the square board ahead of a collapsible betting sheet', async () => {
    const [component, css] = await sources([
        './src/components/MinesGame/MinesGame.jsx',
        './src/components/MinesGame/MinesGame.css',
    ])
    assert.match(component, /<MobileBetSheet[^>]*title="Mines bet controls"/)
    assert.match(component, /mines-bet-sheet/)
    assert.match(component, /mobile-sheet-secondary/)
    assert.match(component, /rootClassName="mines-fairness-modal-portal mobile-game-modal"/)
    assert.match(component, /rootClassName="mines-history-modal-portal mobile-game-modal"/)
    assert.match(css, /\.mines-display\s*\{[^}]*aspect-ratio:\s*1/s)
    assert.match(css, /\.mines-bet-sheet\[data-state='collapsed'\]/)
    assert.match(css, /@media\s*\(max-width:\s*768px\)/)
})
```

- [ ] **Step 2: Run Mines RED**

Run:

```bash
node --test --test-name-pattern="Mines keeps" mobile-ui.test.mjs
```

Expected: FAIL because Mines is not wrapped in the shared sheet.

- [ ] **Step 3: Wrap the existing sidebar without touching game state**

In `MinesGame.jsx`, add:

```jsx
import MobileBetSheet from '../MobileBetSheet'
```

In `MinesGame.jsx`, insert `<MobileBetSheet title="Mines bet controls" className="mines-bet-sheet">` immediately before the current `<div className="mines-sidebar">`, then insert `</MobileBetSheet>` immediately after that div's closing tag and before the `mines-display-wrapper` comment. Do not move or alter `.mines-sidebar-content`, `.sidebar-footer`, descendant JSX, state, handlers, or modal content.

Add `mobile-sheet-secondary` to the existing `.bet-mode-tabs`, Mines selector `.form-group`, Gems `.form-group`, Total Profit `.form-group`, Random Pick button, and `.sidebar-footer`. Do not add it to the Bet Amount group or `.btn-bet-mines`, so Bet/Cashout remains visible while collapsed.

Change the existing modal portal values to `rootClassName="mines-fairness-modal-portal mobile-game-modal"` and `rootClassName="mines-history-modal-portal mobile-game-modal"`; never add a second `rootClassName` prop.

- [ ] **Step 4: Replace only the mobile Mines layout rules**

In `MinesGame.css`, keep desktop rules and add after them:

```css
@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .mines-game {
        min-height: calc(100dvh - var(--mobile-header-height) - var(--mobile-nav-space));
        padding-bottom: 196px;
    }

    .mines-game .game-container {
        display: block;
        overflow: visible;
    }

    .mines-game .mines-display-wrapper {
        min-height: auto;
        overflow: visible;
    }

    .mines-game .mines-display {
        width: min(100%, 560px);
        max-height: none;
        aspect-ratio: 1;
        padding: 12px;
    }

    .mines-game .mines-grid {
        gap: clamp(5px, 2vw, 8px);
        padding: 4px;
    }

    .mines-game .mine-tile {
        border-radius: 9px;
    }

    .mines-bet-sheet .mines-sidebar {
        width: 100%;
        min-width: 0;
        border: 0;
    }

    .mines-bet-sheet[data-state='collapsed'] .mines-sidebar-content {
        overflow: hidden;
    }

    .mobile-game-modal .ant-modal {
        width: calc(100vw - 24px) !important;
        max-width: none;
        margin: 12px auto;
        padding-bottom: 0;
    }

    .mobile-game-modal .ant-modal-content {
        max-height: calc(100dvh - 24px);
        overflow: auto;
    }
}
```

- [ ] **Step 5: Verify Mines tests and gameplay**

Run:

```bash
node --test --test-name-pattern="Mines keeps" mobile-ui.test.mjs
```

Expected: PASS.

Browser-check at `320×568`, `390×844`, and landscape: grid remains square and fully reachable; sheet expands/collapses and closes with `Escape`; Bet starts a game; selected cells remain visible; Cashout remains reachable; no wallet or fairness behavior changes.

---

### Task 6: Convert Crash to chart-first mobile layout

**Files:**
- Modify: `src/components/CrashGame/CrashGame.jsx`
- Modify: `src/components/CrashGame/BettingPanel.jsx`
- Modify: `src/components/CrashGame/GameHistory.jsx`
- Modify: `src/components/CrashGame/CrashGame.css`
- Test: `mobile-ui.test.mjs`

**Interfaces:**
- Consumes: `MobileBetSheet`, `PlayerBets`, `PlayerResults`, current Crash phase and betting callbacks.
- Produces: `.crash-bet-sheet`; mobile-only Bets/Results tabs; always-visible Bet/Cash Out control; horizontal history rail.

- [ ] **Step 1: Add the failing Crash contract**

Append:

```js
test('Crash prioritizes chart, cashout, and mobile player tabs', async () => {
    const [game, panel, history, css] = await sources([
        './src/components/CrashGame/CrashGame.jsx',
        './src/components/CrashGame/BettingPanel.jsx',
        './src/components/CrashGame/GameHistory.jsx',
        './src/components/CrashGame/CrashGame.css',
    ])
    assert.match(game, /<MobileBetSheet[^>]*title="Crash bet controls"/)
    assert.match(game, /mobileDataTab/)
    assert.match(game, /crash-mobile-tabs/)
    assert.match(game, /showPlayerBets && mobileDataTab === 'bets'/)
    assert.match(panel, /mobile-sheet-secondary/)
    assert.match(history, /crash-history-drawer-portal mobile-game-modal/)
    assert.match(css, /\.game-history-bar[\s\S]*overflow-x:\s*auto/)
    assert.match(css, /\.crash-mobile-tabs/)
})
```

- [ ] **Step 2: Run Crash RED**

Run:

```bash
node --test --test-name-pattern="Crash prioritizes" mobile-ui.test.mjs
```

Expected: FAIL.

- [ ] **Step 3: Add presentation-only mobile state and sheet wrapper**

In `CrashGame.jsx`, add:

```jsx
import MobileBetSheet from '../MobileBetSheet'
```

Add near `PHASE`:

```jsx
const MOBILE_QUERY = '(max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none)'
```

Add with other UI state:

```jsx
const [mobileDataTab, setMobileDataTab] = useState('bets')
const [isMobileLayout, setIsMobileLayout] = useState(() =>
    window.matchMedia(MOBILE_QUERY).matches,
)
```

Add this presentation-only effect:

```jsx
useEffect(() => {
    const media = window.matchMedia(MOBILE_QUERY)
    const update = () => setIsMobileLayout(media.matches)
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
}, [])
```

Insert `<MobileBetSheet title="Crash bet controls" className="crash-bet-sheet">` immediately before the current `<div className="crash-sidebar">`, then insert `</MobileBetSheet>` immediately after that div's closing tag and before the Game Display comment. Keep the existing `BettingPanel` and complete footer JSX unchanged. Replace only the current `showPlayerBets && (` condition with `showPlayerBets && !isMobileLayout && (`; keep the current `PlayerBets` props exactly as they are.

Replace the current chart PlayerResults with this desktop-only condition, then add the mobile tab section immediately after it:

```jsx
{showPlayerResults && !isMobileLayout && (
    <PlayerResults cashouts={playerCashouts} />
)}

{isMobileLayout && (
    <section className="crash-mobile-tabs" aria-label="Crash player data">
        <div role="tablist" aria-label="Player data">
            {['bets', 'results'].map((tab, index, tabs) => (
                <button
                    key={tab}
                    id={`crash-${tab}-tab`}
                    type="button"
                    role="tab"
                    tabIndex={mobileDataTab === tab ? 0 : -1}
                    aria-selected={mobileDataTab === tab}
                    aria-controls={`crash-${tab}-panel`}
                    onClick={() => setMobileDataTab(tab)}
                    onKeyDown={(event) => {
                        if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return
                        event.preventDefault()
                        const direction = event.key === 'ArrowRight' ? 1 : -1
                        const nextTab = tabs[(index + direction + tabs.length) % tabs.length]
                        setMobileDataTab(nextTab)
                        document.getElementById(`crash-${nextTab}-tab`)?.focus()
                    }}
                >
                    {tab === 'bets' ? 'Bets' : 'Results'}
                </button>
            ))}
        </div>
        <div
            id={`crash-${mobileDataTab}-panel`}
            role="tabpanel"
            aria-labelledby={`crash-${mobileDataTab}-tab`}
        >
            {showPlayerBets && mobileDataTab === 'bets' ? (
                <PlayerBets
                    phase={phase}
                    multiplier={multiplier}
                    onPlayerCashout={handlePlayerCashout}
                    userBetData={userBetData}
                />
            ) : mobileDataTab === 'results' && showPlayerResults ? (
                <PlayerResults cashouts={playerCashouts} />
            ) : null}
        </div>
    </section>
)}
```

This keeps exactly one active `PlayerBets` instance and preserves the existing callback props.

Change the existing values to `rootClassName="crash-history-modal-portal mobile-game-modal"` and `rootClassName="crash-fairness-modal-portal mobile-game-modal"`; never add a second `rootClassName` prop. Add `rootClassName="crash-history-drawer-portal mobile-game-modal"` to the existing value in `GameHistory.jsx`, and add that file to this task's modify list.

- [ ] **Step 4: Mark noncritical collapsed content in `BettingPanel.jsx`**

Add `mobile-sheet-secondary` to:

```jsx
<div className="form-group mobile-sheet-secondary">
    {/* Auto Cashout */}
</div>

<div className="profit-card-3d mobile-sheet-secondary">
```

The Bet/Cash Out button and Bet Amount remain unmarked so they stay visible while collapsed.

- [ ] **Step 5: Add chart-first CSS**

Append to `CrashGame.css`:

```css
.crash-mobile-tabs {
    display: none;
}

@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .crash-game {
        padding-bottom: 196px;
    }

    .crash-game .game-container {
        display: block;
        overflow: visible;
    }

    .crash-game .game-display {
        width: 100%;
        min-height: 420px;
    }

    .crash-bet-sheet .crash-sidebar {
        width: 100%;
        min-width: 0;
        border: 0;
    }

    .crash-mobile-tabs {
        display: block;
        padding: 10px 12px 18px;
    }

    .crash-mobile-tabs [role='tablist'] {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 10px;
    }

    .crash-mobile-tabs [role='tab'] {
        min-height: 44px;
        border: 1px solid var(--border-default);
        border-radius: 8px;
        background: var(--surface-1);
        color: var(--text-secondary);
    }

    .crash-mobile-tabs [aria-selected='true'] {
        border-color: var(--primary);
        color: var(--text-primary);
    }

    .crash-game .game-history-bar .history-pills-scroll {
        overflow-x: auto;
        overscroll-behavior-inline: contain;
        touch-action: pan-x;
    }
}
```

- [ ] **Step 6: Verify Crash tests and round interaction**

Run:

```bash
node --test --test-name-pattern="Crash prioritizes" mobile-ui.test.mjs
```

Expected: PASS.

Browser-check: Place Bet remains reachable collapsed; when the round runs, Cash Out remains visible and works; history scrolls horizontally; Bets/Results tabs switch without resetting the round; chart is not clipped; dialogs close with `Escape`; desktop sidebar remains unchanged.

---

### Task 7: Convert Dino to game-first mobile layout

**Files:**
- Modify: `src/components/DinoGame/DinoGame.jsx`
- Modify: `src/components/DinoGame/DinoGame.css`
- Test: `mobile-ui.test.mjs`

**Interfaces:**
- Consumes: `MobileBetSheet`, `gamePhase`, existing Phaser container and action callbacks.
- Produces: `.dino-bet-sheet`; sheet auto-collapse during `running`/`waiting`; stable Jump/Cash Out controls; aspect-ratio-safe Phaser container.

- [ ] **Step 1: Add the failing Dino contract**

Append:

```js
test('Dino keeps Phaser and live actions ahead of secondary controls', async () => {
    const [component, css] = await sources([
        './src/components/DinoGame/DinoGame.jsx',
        './src/components/DinoGame/DinoGame.css',
    ])
    assert.match(component, /<MobileBetSheet[^>]*title="Dino bet controls"/)
    assert.match(component, /collapseOn=\{gamePhase === 'running' \|\| gamePhase === 'waiting'\}/)
    assert.match(component, /dino-bet-sheet/)
    assert.match(component, /mobile-sheet-secondary/)
    assert.match(css, /\.phaser-container\s*\{[^}]*aspect-ratio:/s)
    assert.match(css, /orientation:\s*landscape/)
})
```

- [ ] **Step 2: Run Dino RED**

Run:

```bash
node --test --test-name-pattern="Dino keeps" mobile-ui.test.mjs
```

Expected: FAIL.

- [ ] **Step 3: Wrap the current Dino sidebar and mark secondary sections**

In `DinoGame.jsx`, add:

```jsx
import MobileBetSheet from '../MobileBetSheet'
```

Insert the following opening tag immediately before the current `<div className="dino-sidebar">`, then insert `</MobileBetSheet>` immediately after that div's closing tag and before the Game Area comment:

```jsx
<MobileBetSheet
    title="Dino bet controls"
    className="dino-bet-sheet"
    collapseOn={gamePhase === 'running' || gamePhase === 'waiting'}
>
```

Do not move or change any sidebar child, control, or callback. Add `mobile-sheet-secondary` to the existing Last Result card and `.sidebar-footer`. Keep Bet Amount, Difficulty, Place Bet, Jump, Cash Out, and the Current Run card unmarked so live controls remain available.

Change the existing values to `rootClassName="dino-history-modal-portal mobile-game-modal"` and `rootClassName="dino-fairness-modal-portal mobile-game-modal"`; never add a second `rootClassName` prop.

- [ ] **Step 4: Add stable Phaser/mobile layout rules**

Append to `DinoGame.css`:

```css
@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .dino-game-page {
        padding-bottom: 196px;
    }

    .dino-container {
        display: block;
        overflow: visible;
    }

    .dino-game-area {
        width: 100%;
        min-height: 0;
    }

    .phaser-container {
        width: 100%;
        aspect-ratio: 16 / 9;
        overflow: hidden;
    }

    .phaser-container canvas {
        display: block;
        max-width: 100%;
        height: auto !important;
        margin: auto;
    }

    .dino-bet-sheet .dino-sidebar {
        width: 100%;
        min-width: 0;
        max-height: none;
        border: 0;
    }

    .dino-bet-sheet .jump-btn,
    .dino-bet-sheet .bet-button {
        min-height: 48px;
    }
}

@media (max-width: 932px) and (orientation: landscape) {
    .dino-game-page {
        padding-bottom: calc(var(--mobile-nav-space) + 132px);
    }

    .dino-game-area {
        max-width: 860px;
        margin-inline: auto;
    }

    .dino-bet-sheet {
        --mobile-sheet-collapsed-height: 132px;
    }
}
```

Do not edit `DinoGameInstance.resize`, Phaser config, scenes, or core files.

- [ ] **Step 5: Verify Dino tests and runtime**

Run:

```bash
node --test --test-name-pattern="Dino keeps" mobile-ui.test.mjs
```

Expected: PASS.

Browser-check portrait and landscape: Phaser canvas retains aspect ratio; Place Bet starts the game; the sheet collapses once running; Jump and Cash Out remain stable and clear of bottom nav; expanding/collapsing does not recreate the Phaser canvas; orientation changes preserve game state.

---

### Task 8: Adapt the current Plinko playback UI without touching its engine

**Files:**
- Modify: `src/components/PlinkoGame/PlinkoGame.jsx`
- Modify: `src/components/PlinkoGame/Sidebar.jsx`
- Modify: `src/components/PlinkoGame/PlinkoGame.css`
- Modify: `src/components/PlinkoGame/Sidebar.css`
- Modify: `src/components/PlinkoGame/Plinko.css`
- Test: `mobile-ui.test.mjs`
- Test: `plinko-regressions.test.mjs`

**Interfaces:**
- Consumes: the execution-start single-canvas Plinko implementation, current Sidebar props, and `MobileBetSheet`.
- Produces: `.plinko-bet-sheet`; collapsed controls that always expose Drop/Stop; horizontal ball/recent-play rails; exact `760:570` presentation ratio on the existing single canvas.

- [ ] **Step 1: Add the failing Plinko presentation contract**

Append:

```js
test('Plinko mobile presentation preserves board ratio and critical controls', async () => {
    const [game, sidebar, board, gameCss, sidebarCss, boardCss] = await sources([
        './src/components/PlinkoGame/PlinkoGame.jsx',
        './src/components/PlinkoGame/Sidebar.jsx',
        './src/components/PlinkoGame/Plinko.jsx',
        './src/components/PlinkoGame/PlinkoGame.css',
        './src/components/PlinkoGame/Sidebar.css',
        './src/components/PlinkoGame/Plinko.css',
    ])
    assert.match(game, /<MobileBetSheet[^>]*title="Plinko bet controls"/)
    assert.match(game, /plinko-bet-sheet/)
    assert.match(sidebar, /mobile-sheet-secondary/)
    assert.match(gameCss, /\.recent-plays-list\s*\{[^}]*overflow-x:\s*auto/s)
    assert.match(sidebarCss, /\.ball-types-grid\s*\{[^}]*overflow-x:\s*auto/s)
    assert.match(boardCss, /aspect-ratio:\s*760\s*\/\s*570/)
    assert.match(boardCss, /\.plinko-canvas\s*\{[^}]*width:\s*100%\s*!important[^}]*height:\s*100%\s*!important/s)
    assert.equal((board.match(/className="plinko-canvas"/g) || []).length, 1)
})
```

- [ ] **Step 2: Run Plinko RED plus current gameplay baseline**

Run:

```bash
node --test --test-name-pattern="Plinko mobile presentation" mobile-ui.test.mjs
node --test plinko-regressions.test.mjs
```

Expected: mobile contract FAILS; the existing Plinko regression suite PASSES before presentation changes.

- [ ] **Step 3: Wrap only the current sidebar**

In `PlinkoGame.jsx`, add:

```jsx
import MobileBetSheet from '../MobileBetSheet'
```

Replace only the `.plinko-sidebar-wrapper` opening/closing structure with:

```jsx
<MobileBetSheet title="Plinko bet controls" className="plinko-bet-sheet">
    <div className="plinko-sidebar-wrapper">
        <Sidebar
            balance={balance}
            betAmount={betAmount}
            setBetAmount={setBetAmount}
            rowCount={rowCount}
            setRowCount={setRowCount}
            riskLevel={riskLevel}
            setRiskLevel={setRiskLevel}
            hasOutstandingBalls={hasOutstandingBalls}
            onDropBall={handleDropBall}
            onSettingsClick={() => setIsSettingsOpen(!isSettingsOpen)}
            onStatsClick={() => setStatsDrawerOpen(true)}
            isSettingsOpen={isSettingsOpen}
            isStatsOpen={statsDrawerOpen}
            selectedBallType={selectedBallType}
            setSelectedBallType={setSelectedBallType}
            ballTypes={BALL_TYPES}
            currentBall={currentBall}
            lastWin={lastWin}
            winRecords={winRecords}
            currentStreak={currentStreak}
            maxStreak={maxStreak}
            effectiveBetCost={effectiveBetCost}
        />
    </div>
</MobileBetSheet>
```

Retain the prop list above exactly. Change the existing modal portal values to `rootClassName="plinko-history-modal-portal mobile-game-modal"` and `rootClassName="plinko-fairness-modal-portal mobile-game-modal"`; never add a second `rootClassName` prop. Do not edit drop callbacks, refs, engine construction, fairness state, or wallet callbacks.

- [ ] **Step 4: Mark secondary Plinko controls without changing handlers**

In `Sidebar.jsx`, add `mobile-sheet-secondary` to:

- Risk form group.
- Rows form group.
- Number of Bets form group.
- Sidebar footer.
- Ball selector card.

Do not mark:

- Manual/Auto tabs.
- Bet Amount.
- Drop Ball / Start Autobet / Stop Autobet button.

No state or callback code changes in this step.

- [ ] **Step 5: Add mobile Plinko layout rules**

Append to `PlinkoGame.css`:

```css
@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .plinko-page {
        padding-bottom: 196px;
    }

    .plinko-container {
        display: block;
        overflow: visible;
    }

    .plinko-game-wrapper {
        width: 100%;
        min-height: 0;
    }

    .plinko-bet-sheet .plinko-sidebar-wrapper,
    .plinko-bet-sheet .sidebar {
        width: 100%;
        min-width: 0;
        max-height: none;
    }

    .recent-plays-list {
        display: flex;
        overflow-x: auto;
        overscroll-behavior-inline: contain;
        scrollbar-width: none;
        touch-action: pan-x;
    }

    .recent-plays-list > * {
        flex: 0 0 auto;
    }

    .debug-path-row {
        overflow-x: auto;
        overscroll-behavior-inline: contain;
    }
}
```

Append to `Sidebar.css`:

```css
@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .plinko-bet-sheet .sidebar {
        padding: 10px 12px 16px;
    }

    .plinko-bet-sheet .bet-button {
        min-height: 48px;
    }

    .plinko-bet-sheet .ball-types-grid {
        display: flex;
        overflow-x: auto;
        overscroll-behavior-inline: contain;
        scrollbar-width: none;
        touch-action: pan-x;
    }

    .plinko-bet-sheet .ball-type-option {
        flex: 0 0 min(210px, 72vw);
    }
}
```

In `Plinko.css`, extend the existing mobile board rules with:

```css
@media (max-width: 768px), (max-width: 932px) and (orientation: landscape) and (hover: none) {
    .plinko-board-wrapper,
    .plinko-canvas-container {
        width: 100%;
        aspect-ratio: 760 / 570;
    }

    .plinko-canvas {
        display: block;
        width: 100% !important;
        height: 100% !important;
    }
}
```

- [ ] **Step 6: Verify Plinko mobile and all gameplay contracts GREEN**

Run:

```bash
node --test --test-name-pattern="Plinko mobile presentation" mobile-ui.test.mjs
node --test plinko-regressions.test.mjs
```

Expected: both commands pass. Do not create any additional Plinko engine, asset generator, or gameplay test as part of mobile work. Compare all protected Plinko status and non-presentation diffs with Task 1's baseline before continuing.

- [ ] **Step 7: Browser-verify Plinko mobile behavior**

At `320×568`, `390×844`, and landscape:

- Board and bins fit without horizontal cropping.
- The single `.plinko-canvas` remains inside a `760:570` container and its rendered rectangle fits the board without cropping.
- Drop Ball remains visible collapsed.
- Start/Stop Autobet remains visible collapsed and Stop works.
- Expanded sheet exposes Risk, Rows, Number of Bets, and horizontal Ball Type cards.
- Debug path scrolls horizontally while target bin remains readable.
- Drop one ball and verify Debug L/R path and final bin still match.
- Rapidly click 100 times and confirm no more than 20 charges/active-pending drops.
- Confirm no runtime exception.

---

### Task 9: Add repeatable CDP verification for all routes and viewports

**Files:**
- Create: `scripts/verifyMobileUi.mjs`
- Test: live Vite app through Chrome DevTools Protocol.

**Interfaces:**
- Consumes environment variables: `MOBILE_APP_ORIGIN` defaulting to `http://127.0.0.1:5210`, `MOBILE_CDP_PORT` defaulting to `9340`.
- Produces: JSON route/viewport report; exits nonzero on overflow, shell visibility mismatch, failed drawer/sheet behavior, runtime exception, changed Plinko canvas count, incorrect board ratio, or canvas cropping.

- [ ] **Step 1: Create the browser verifier**

Create `scripts/verifyMobileUi.mjs`:

```js
import assert from 'node:assert/strict'

const origin = process.env.MOBILE_APP_ORIGIN || 'http://127.0.0.1:5210'
const cdpPort = process.env.MOBILE_CDP_PORT || '9340'
const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json/list`)).json()
const target = targets.find(item => item.type === 'page')
assert.ok(target, 'Chrome page target not found')

const ws = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true })
    ws.addEventListener('error', reject, { once: true })
})

let id = 0
const pending = new Map()
const runtimeErrors = []
ws.addEventListener('message', ({ data }) => {
    const message = JSON.parse(data)
    if (message.id) {
        const request = pending.get(message.id)
        if (!request) return
        pending.delete(message.id)
        message.error
            ? request.reject(new Error(message.error.message))
            : request.resolve(message.result)
    } else if (message.method === 'Runtime.exceptionThrown') {
        runtimeErrors.push(message.params.exceptionDetails.text)
    }
})

function send(method, params = {}) {
    const requestId = ++id
    ws.send(JSON.stringify({ id: requestId, method, params }))
    return new Promise((resolve, reject) => pending.set(requestId, { resolve, reject }))
}

async function evaluate(expression) {
    const { result, exceptionDetails } = await send('Runtime.evaluate', {
        expression,
        awaitPromise: true,
        returnByValue: true,
    })
    if (exceptionDetails) throw new Error(exceptionDetails.exception?.description || exceptionDetails.text)
    return result.value
}

async function waitFor(expression, timeout = 30000) {
    return evaluate(`new Promise((resolve, reject) => {
        const deadline = performance.now() + ${timeout}
        const check = () => {
            try { if (${expression}) return resolve(true) } catch {}
            if (performance.now() > deadline) return reject(new Error('Timed out: ${expression}'))
            setTimeout(check, 50)
        }
        check()
    })`)
}

await Promise.all([send('Runtime.enable'), send('Page.enable')])

const routes = ['/', '/mines', '/crash', '/dino', '/plinko']
const viewports = [
    { width: 320, height: 568, label: 'phone-small', mobile: true, expectMobileShell: true },
    { width: 375, height: 667, label: 'phone-medium', mobile: true, expectMobileShell: true },
    { width: 390, height: 844, label: 'phone', mobile: true, expectMobileShell: true },
    { width: 430, height: 932, label: 'phone-large', mobile: true, expectMobileShell: true },
    { width: 820, height: 1180, label: 'tablet-portrait', mobile: true, expectMobileShell: false },
    { width: 844, height: 390, label: 'touch-landscape', mobile: true, expectMobileShell: true },
    { width: 1280, height: 800, label: 'desktop', mobile: false, expectMobileShell: false },
]
const report = []

for (const viewport of viewports) {
    await send('Emulation.setDeviceMetricsOverride', {
        width: viewport.width,
        height: viewport.height,
        deviceScaleFactor: 1,
        mobile: viewport.mobile,
        screenOrientation: {
            type: viewport.width > viewport.height ? 'landscapePrimary' : 'portraitPrimary',
            angle: viewport.width > viewport.height ? 90 : 0,
        },
    })
    await send('Emulation.setTouchEmulationEnabled', {
        enabled: viewport.mobile,
        maxTouchPoints: viewport.mobile ? 5 : 1,
    })

    for (const route of routes) {
        await send('Page.navigate', { url: `${origin}${route}` })
        await waitFor(`document.readyState === 'complete' && document.querySelector('.main-content')`)
        await evaluate(`new Promise(resolve => setTimeout(resolve, 400))`)

        const result = await evaluate(`(() => {
            const nav = document.querySelector('.mobile-bottom-nav')
            const header = document.querySelector('.header')
            const sheet = document.querySelector('.mobile-bet-sheet')
            const canvas = document.querySelector('.plinko-canvas')
            const canvasContainer = document.querySelector('.plinko-canvas-container')
            const canvasRect = canvas?.getBoundingClientRect()
            const containerRect = canvasContainer?.getBoundingClientRect()
            return {
                route: location.pathname,
                overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                navLinks: nav ? nav.querySelectorAll('a').length : 0,
                navVisible: nav ? getComputedStyle(nav).display !== 'none' : false,
                headerTop: header?.getBoundingClientRect().top,
                sheet: Boolean(sheet),
                canvasCount: document.querySelectorAll('.plinko-canvas').length,
                canvasRatio: containerRect ? containerRect.width / containerRect.height : null,
                canvasFits: canvasRect && containerRect
                    ? canvasRect.left >= containerRect.left - 1 &&
                        canvasRect.right <= containerRect.right + 1 &&
                        canvasRect.top >= containerRect.top - 1 &&
                        canvasRect.bottom <= containerRect.bottom + 1
                    : null,
            }
        })()`)

        assert.ok(result.overflow <= 1, `${viewport.label} ${route} overflows by ${result.overflow}px`)
        assert.equal(result.navLinks, 5, `${route} nav count`)
        assert.equal(result.navVisible, viewport.expectMobileShell, `${route} nav visibility`)
        assert.equal(result.headerTop >= 0, true, `${route} header clipped`)

        if (viewport.expectMobileShell && route !== '/') {
            assert.equal(result.sheet, true, `${route} missing betting sheet`)
            await evaluate(`document.querySelector('.mobile-bet-sheet__handle').click()`)
            await waitFor(`document.querySelector('.mobile-bet-sheet')?.dataset.state === 'expanded'`)
            const expanded = await evaluate(`(() => {
                const sheet = document.querySelector('.mobile-bet-sheet')
                return sheet.contains(document.activeElement) && sheet.getAttribute('aria-modal') === 'true'
            })()`)
            assert.equal(expanded, true, `${route} sheet focus/modal state`)
            await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape' })
            await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape' })
            await waitFor(`document.querySelector('.mobile-bet-sheet')?.dataset.state === 'collapsed'`)
        }

        if (viewport.expectMobileShell && route === '/') {
            await evaluate(`document.querySelector('.mobile-menu-button').click()`)
            await waitFor(`document.querySelector('.mobile-menu-button')?.getAttribute('aria-expanded') === 'true'`)
            await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape' })
            await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape' })
            await waitFor(`document.querySelector('.mobile-menu-button')?.getAttribute('aria-expanded') === 'false'`)
        }

        if (viewport.expectMobileShell && route === '/mines') {
            await evaluate(`document.querySelector('.mobile-wallet-balance').click()`)
            await waitFor(`document.querySelector('.wallet-dropdown')`)
            const walletFits = await evaluate(`(() => {
                const rect = document.querySelector('.wallet-dropdown').getBoundingClientRect()
                return rect.left >= 0 && rect.right <= innerWidth && rect.bottom <= innerHeight
            })()`)
            assert.equal(walletFits, true, 'wallet dropdown exceeds viewport')
            await evaluate(`document.querySelector('.wallet-close-btn').click()`)
        }

        if (route === '/plinko') {
            assert.equal(result.canvasCount, 1, 'Plinko canvas count changed')
            assert.ok(Math.abs(result.canvasRatio - 760 / 570) < 0.02, 'Plinko ratio changed')
            assert.equal(result.canvasFits, true, 'Plinko canvas exceeds its container')
        }
        report.push({ viewport: viewport.label, ...result })
    }
}

assert.deepEqual(runtimeErrors, [])
console.log(JSON.stringify({ report, runtimeErrors }, null, 2))
ws.close()
```

- [ ] **Step 2: Run the complete browser matrix**

With Vite and Chrome still running on `5210/9340`, run:

```bash
node scripts/verifyMobileUi.mjs
```

Expected: exit 0; 35 route/viewport entries; no overflow; exactly five nav links with mobile visibility at four phone sizes and touch landscape; hidden mobile nav at tablet and desktop; each mobile game sheet expands/focuses/collapses; the wallet panel fits; Plinko retains one uncropped `760:570` canvas; no runtime exceptions.

- [ ] **Step 3: Manually exercise interactions the geometry script cannot prove**

At `390×844`, verify with actual clicks:

- Drawer focus and `Escape` behavior.
- Wallet panel remains within viewport.
- Each betting sheet expands, traps focus, collapses with `Escape`, and restores focus.
- Mines Bet/Cashout.
- Crash Bet/Cash Out during a round.
- Dino Start/Jump/Cash Out and no Phaser recreation.
- Plinko Drop/Auto/Stop and exact fairness result.
- Palette changes persist across all routes.

Expected: all interactions work without console exceptions.

---

### Task 10: Final regression, external build, and protected-file audit

**Files:**
- Verify all changed source/test files.
- Do not modify: `dist/**` and all engine/fairness/wallet files listed above.

**Interfaces:**
- Consumes: completed mobile implementation.
- Produces: fresh automated, browser, build, and Git evidence; no commit or push.

- [ ] **Step 1: Run all mobile and existing regressions**

Run:

```bash
node --test mobile-ui.test.mjs vite.config.test.mjs src/components/sidebar.test.mjs plinko-regressions.test.mjs
git -c core.whitespace=cr-at-eol diff --check
```

Expected: all tests pass and the whitespace check emits no output.

- [ ] **Step 2: Build outside the repository**

Run:

```bash
BUILD_DIR="${TMPDIR:-/tmp}/stake-mobile-build"
ls "${TMPDIR:-/tmp}"
npm run build -- --outDir "$BUILD_DIR" --emptyOutDir
```

Expected: Vite exits 0 and writes only to the external temporary path.

- [ ] **Step 3: Re-run the CDP matrix against the final source**

Run:

```bash
node scripts/verifyMobileUi.mjs
```

Expected: exit 0 with all 35 entries, no runtime exceptions, no overflow, and no shell/sheet/wallet/canvas failures.

- [ ] **Step 4: Compare protected engine, fairness, wallet, and generated paths with Task 1**

Run in the same shell or restore the same variable value first:

```bash
BASELINE_DIR="${TMPDIR:-/tmp}/stake-mobile-baseline"
git status --short -- src/context/WalletContext.jsx src/utils/ProvablyFair.js src/components/PlinkoGame/PlinkoEngine.js src/components/PlinkoGame/Ball.js src/components/PlinkoGame/dropPlinkoBall.js src/components/DinoGame/core public/plinko-outcomes.json scripts/generatePlinkoOutcomes.cjs > "$BASELINE_DIR/protected-status-after.txt"
git diff --binary -- src/context/WalletContext.jsx src/utils/ProvablyFair.js src/components/PlinkoGame/PlinkoEngine.js src/components/PlinkoGame/Ball.js src/components/PlinkoGame/dropPlinkoBall.js src/components/DinoGame/core public/plinko-outcomes.json scripts/generatePlinkoOutcomes.cjs > "$BASELINE_DIR/protected-diff-after.patch"
diff -u "$BASELINE_DIR/protected-status-before.txt" "$BASELINE_DIR/protected-status-after.txt"
diff -u "$BASELINE_DIR/protected-diff-before.patch" "$BASELINE_DIR/protected-diff-after.patch"
```

Expected: both comparisons exit 0 with no output. Apply the same before/after comparison to every extra protected path added at execution start.

- [ ] **Step 5: Prove `dist` is untouched using status and binary diff**

Run:

```bash
git status --short -- dist > "$BASELINE_DIR/dist-status-after.txt"
git diff --binary -- dist > "$BASELINE_DIR/dist-diff-after.patch"
diff -u "$BASELINE_DIR/dist-status-before.txt" "$BASELINE_DIR/dist-status-after.txt"
diff -u "$BASELINE_DIR/dist-diff-before.patch" "$BASELINE_DIR/dist-diff-after.patch"
```

Expected: both comparisons exit 0 with no output.

- [ ] **Step 6: Audit the allowed Plinko presentation boundary**

Run:

```bash
git status --short -- src/components/PlinkoGame public scripts '*plinko*.test.mjs'
git diff --name-only -- src/components/PlinkoGame public scripts '*plinko*.test.mjs'
```

Expected: any new mobile diff is limited to `PlinkoGame.jsx`, `Sidebar.jsx`, `PlinkoGame.css`, `Sidebar.css`, and `Plinko.css`; every execution-start diff remains represented in Task 1's `plinko-status-before.txt` and `plinko-diff-before.patch`.

- [ ] **Step 7: Report final working-tree state without committing**

Run:

```bash
git status --short
```

Expected: only the planned mobile source/tests plus the untracked spec/plan documents and any execution-start changes are present; no commit or push occurs.
