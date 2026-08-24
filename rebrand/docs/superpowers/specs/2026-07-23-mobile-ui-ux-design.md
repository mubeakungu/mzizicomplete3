# Mobile UI/UX Design

**Status:** Approved

**Goal:** Add a complete mobile experience to the five existing routes without changing game logic, wallet behavior, fairness behavior, or desktop UX.

## Scope

The implementation covers these routes in this order:

1. Shared application shell
2. `/` — Home
3. `/mines` — Mines
4. `/crash` — Crash
5. `/dino` — Dino
6. `/plinko` — Plinko

The sidebar links `/favourites`, `/recent`, `/challenges`, and `/my-bets` remain out of scope because no corresponding routes exist. On mobile, they appear as disabled items marked “Coming soon” and must not navigate to an empty page.

The work must preserve all current uncommitted Plinko changes. It must not modify `dist` or run a production build into the repository’s default output directory.

## Responsive Architecture

Use the existing components and game implementations. Add a shared mobile shell, then adapt each page through route-specific layout and CSS changes. Do not create duplicate mobile versions of game components and do not introduce a generic game abstraction that requires refactoring all four games.

The primary mobile breakpoint is `768px`. The implementation must also work at narrow widths from `320px` and tablet widths from `769px` through `1024px`.

Desktop behavior above `768px` remains unchanged unless a shared accessibility correction is necessary.

## Shared Mobile Shell

### Header

At widths up to `768px`, the header is approximately `52px` tall and contains:

- Logo or home affordance on the left.
- Wallet balance in the primary visible area.
- A menu button that opens the mobile drawer.

Search, palette selection, and secondary icon actions move into the drawer when they do not fit. The wallet panel must fit within the viewport and must not create horizontal scrolling.

### Bottom Navigation

A fixed bottom navigation provides one-tap access to:

- Home
- Crash
- Plinko
- Dino
- Mines

The active route is visually and programmatically identified. Each target is at least `44×44px`. The navigation accounts for `env(safe-area-inset-bottom)` and never covers page content.

### Drawer

The menu button opens a mobile drawer containing:

- Search.
- Palette selection.
- Secondary header actions.
- Favourites, Recent, Challenges, and My Bets as disabled “Coming soon” items.

Opening the drawer locks background scrolling and traps focus. Closing it by its close control, backdrop, or `Escape` returns focus to the menu button.

### Viewport and Scrolling

Declare `height: 100vh` first, then override it with `height: 100dvh` so older browsers retain the static viewport fallback. The application shell remains viewport-sized while route content owns vertical scrolling. Every route includes enough bottom padding for the fixed navigation and safe area.

No mobile route may introduce horizontal page scrolling.

## Shared Mobile Game Pattern

All four games use a game-first layout:

1. The game board, chart, or canvas appears first.
2. Primary game status remains visible near the game area.
3. Betting controls live in a bottom sheet below or over the lower edge of the viewport without covering critical game content.

The betting sheet supports three explicit states:

- Closed when the route permits it.
- Collapsed with the minimum controls required to play or stop.
- Expanded with all secondary controls.

The sheet can be closed or collapsed with an explicit control, a downward swipe where practical, or `Escape`. Opening it locks background scrolling and contains keyboard focus. Sheet animation must not trigger repeated canvas resizing or alter any game loop.

## Route Designs

### `/` — Home

- Convert the hero to a compact vertical layout so game cards appear early.
- Keep search in the header or drawer instead of allocating a separate mobile row.
- Render category chips as a horizontally scrollable row.
- Render game cards in two columns on typical phones and one column below approximately `360px`.
- Preserve image aspect ratios and readable game names/statuses.
- Reduce padding and gaps without changing the existing visual identity.
- Ensure the final row of cards remains fully visible above the bottom navigation.

### `/mines` — Mines

- Place the Mines grid before the betting sheet.
- Keep the grid square, centered, and within the viewport width.
- Preserve readable cell gaps and touch targets without horizontal overflow.
- The collapsed betting sheet shows bet amount and the primary action.
- The expanded sheet contains the remaining bet and mine controls.
- Primary actions are full-width and at least `48px` tall.
- Move stats, debug, and fairness content into accordions or near-full-screen dialogs.
- During play, the sheet must not cover selected cells or the win/loss state.
- Landscape mode uses the available width for the grid and keeps controls below it.

### `/crash` — Crash

- Make the chart the primary full-width content below the header.
- Keep multiplier, round state, and countdown inside or immediately adjacent to the chart without adding a tall panel.
- Render multiplier history as a horizontally scrollable chip row.
- The collapsed betting sheet always exposes bet amount and Bet/Cash Out.
- Cash Out remains visible while a round is active.
- Auto Bet and secondary controls appear in the expanded sheet.
- Player bets and results become tabs below the chart instead of side-by-side panels.
- Stats and related dialogs use a near-full-screen mobile presentation with a persistent close control.
- Do not change round timing, state transitions, or cash-out logic.

### `/dino` — Dino

- Place the Phaser canvas first and preserve its aspect ratio.
- Scale the canvas to its container without stretching or horizontal scrolling.
- Keep direct controls such as Jump large and clear of the bottom navigation.
- The collapsed betting sheet shows bet amount, difficulty, and Start.
- The expanded sheet contains Auto Bet, milestone settings, and secondary options.
- Automatically collapse the sheet while the game is running without changing its stored values.
- Keep Jump in a stable position during gameplay.
- Do not resize the Phaser canvas continuously during sheet animation.
- In landscape, enlarge the canvas area and compact nonessential shell controls.
- Do not change Phaser scenes, physics, or the game loop.

### `/plinko` — Plinko

- Place the board first and preserve its `760:570` aspect ratio.
- Keep the static and dynamic canvases exactly aligned.
- Scale the board through presentation layout only; do not alter trajectory coordinates, physics constants, canvas engine behavior, or fairness data.
- Keep payout bins visible with the board and prevent horizontal cropping.
- The collapsed betting sheet shows Bet Amount, Manual/Auto, and Drop/Stop.
- The expanded sheet contains Risk, Rows, Number of Bets, and Ball Type.
- Stop Autobet remains visible whenever Auto Bet is active.
- Risk and Rows retain their existing disabled behavior during active or pending play.
- Render Ball Type as a horizontally scrollable card row.
- Render Recent Plays as horizontally scrollable chips or cards below the board.
- Open Settings, Stats, Fairness, and Debug in near-full-screen mobile dialogs.
- Keep Debug target bin and payout visible while the L/R path scrolls horizontally.
- In landscape, prioritize the board and collapse the betting sheet to one compact control row.

The mobile work must not alter:

- Fairness path generation.
- Trajectory generation or playback.
- The 20-ball active/pending cap.
- Wallet charging or payout semantics.
- Auto Bet cadence or cancellation behavior.
- Payout tables or special-ball behavior.

## Interaction and Accessibility

- Interactive targets are at least `44×44px`; primary game actions are at least `48px` tall.
- No feature depends on hover as its only interaction.
- Drawer, sheet, accordion, tabs, and dialogs expose correct labels, state, and keyboard behavior.
- Focus remains visible and is restored after overlays close.
- Background content is inert or otherwise unavailable while a modal overlay is open.
- Respect `prefers-reduced-motion` for shell, drawer, and sheet animations.
- Account for `env(safe-area-inset-top)` and `env(safe-area-inset-bottom)`.
- Loading and error states must remain visible and must not result in a blank page.
- Game canvas accessibility behavior must not regress from the current implementation.

## State and Error Handling

Responsive layout state is presentation-only. Route changes close the drawer and reset transient sheet presentation state without resetting game, form, wallet, or fairness data.

If viewport or orientation changes while a game is active:

- Preserve game state and control values.
- Recalculate presentation dimensions once the layout settles.
- Keep the game surface aligned and visible.
- Do not restart rounds or reinitialize fairness state.

Existing game errors continue to use their current error paths. Mobile dialogs and sheets must remain closable when an error is shown.

## Verification

Implement and verify one stage before moving to the next:

1. Shared shell.
2. Home.
3. Mines.
4. Crash.
5. Dino.
6. Plinko.

Test at minimum:

- `320×568`
- `375×667`
- `390×844`
- `430×932`
- A tablet portrait viewport.
- A representative landscape viewport.
- Desktop above `768px` for regressions.

Every route must verify:

- No horizontal page scrolling.
- Header and bottom navigation do not cover content.
- Drawer and sheet opening, closing, focus, and keyboard behavior.
- Touch targets and primary actions remain reachable.
- Route changes work through bottom navigation.
- Existing gameplay and wallet behavior remain unchanged.

Crash, Dino, and Plinko must verify chart/canvas size and alignment before and after resize and orientation changes.

Plinko must rerun all existing trajectory, fairness, capacity, and Auto Bet tests. Browser verification must confirm that both Plinko canvases remain aligned and that the mobile presentation does not alter the fairness path or final bin.

Run production builds only with an external `--outDir` outside the repository. Compare Git state before and after verification to prove that `dist` and the existing uncommitted Plinko work were not unintentionally changed.

## Non-Goals

- Creating Favourites, Recent, Challenges, or My Bets pages.
- Changing desktop visual design.
- Rewriting game engines or state management.
- Adding dependencies when CSS, React, and existing Ant Design components are sufficient.
- Changing payouts, wallet rules, fairness, or game timing.
- Modifying generated `dist` files.
