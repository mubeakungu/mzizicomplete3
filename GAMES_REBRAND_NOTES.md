# Rebrand games — build + real wallet wiring

## What was wrong

`rebrand/` was React source that had never been built (`app/static/games/`
didn't exist, so `/games/*` 404'd), and even once built, its wallet
(`WalletContext.jsx`) was a **fake browser-only balance** — `localStorage`,
starting at 1000.00, zero calls to your Flask backend. Two catalog slugs
(`mines`, `plinkomzizi`) were also pointed at this fake demo instead of the
real, wallet-integrated backends already sitting unused elsewhere in your
codebase.

## What's fixed now

- **`registry.py`**: `mines` → `games/mines.html` (real, uses
  `/api/casino/init-round`+`settle-round`). `plinkomzizi` → `/plinko-mzizi/`
  (its own blueprint, own DB models, real wallet debits). `mzizicrash` was
  already correct, untouched.
- **`rebrand/` built for real**: `vite.config.js` now outputs to
  `app/static/games/` under the `/games/` base path Flask expects. Two
  files that were referenced but missing (`ThemeContext.jsx`, `isGamePath`)
  turned out to already exist in the complete project you sent — no
  guessing needed once I had the real source.
- **The wallet is now real money**, for Crash (`jetx` slug) and Dino
  (`dino` slug): `WalletContext.jsx` calls `/api/casino/get-balance` on
  load, `/api/casino/init-round` when a bet is placed (debits the real
  Wallet row), and `/api/casino/settle-round` when a round pays out
  (credits it). The `placeBet`/`addWinnings` functions still return/behave
  synchronously — same call sites the game code already had — but they now
  fire the real API call in the background and reconcile the on-screen
  balance to whatever the server confirms, rather than trusting the
  client's own math forever.
- Added `GET /api/casino/game-by-slug/<slug>` so the frontend resolves a
  game's numeric id from its catalog slug instead of hardcoding one.
- **Mines and Plinko inside the rebrand now redirect** (`/games/mines` →
  `/casino/play/mines`, `/games/plinko` → `/plinko-mzizi/`) instead of
  running a second, un-linked live-money implementation of a game that
  already has a canonical one — matches the "one canonical implementation
  per game" rule already stated in `casino.py`.
- Dropped the unrelated Google Tag Manager snippet and Vercel Analytics
  import that were in the standalone/Vercel version of this repo — this
  isn't a public demo site anymore, it's mounted inside your real casino.

## One real gap left — worth knowing before this carries real stakes

`settle-round` accepts whatever `payout` the client reports and only caps
it at 100x the stake as an anti-fraud ceiling — it does **not** recompute
the crash multiplier or Dino score server-side from the seeds it issued at
`init-round`. That's not something I introduced: it's the same trust model
already live for dice/roulette/slots via this same endpoint. But it does
mean a modified client could claim a fake win up to 100x their stake and
get paid. Hardening this properly means recomputing the actual game
outcome server-side from `server_seed` + `client_seed` + `nonce` (the same
algorithm `ProvablyFair.js` uses client-side for verification) before
trusting the payout — worth doing before real volume goes through Crash
and Dino specifically, since those are the two now live.

## Building it yourself going forward

```bash
cd rebrand
npm install
npm run build     # outputs into ../app/static/games/
```

No other steps — Flask serves the result automatically via
`games_static.py`.
