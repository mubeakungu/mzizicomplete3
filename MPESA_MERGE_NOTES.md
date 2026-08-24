# Merge notes — enhanced crash game + real M-Pesa

This project folder is `mzizifeature_output` with two things merged in:

1. The "enhanced crash" deployment package (from `files__20_.zip`):
   `app/routes/mzizicrash_blueprint.py` (leaderboard, game history, connected
   players), `app/games/strategies.py` (5 staking-plan calculators), and a
   new `strategy_performance` table.
2. A real Safaricom Daraja M-Pesa integration wired into the wallet — this
   was previously stubbed out (see the old comments that are now gone from
   `config.py` / `app/routes/wallet.py`).

Nothing else from the original project was touched — sports betting, the
Unity aviator game, casino lobby, admin dashboard, and auth are unchanged.

## What actually changed

- `app/routes/mzizicrash_blueprint.py` — replaced with the enhanced version;
  added `strategy_name` tagging on `/crash/api/bet` (record-keeping only —
  it never auto-places bets) and two new endpoints:
  `/crash/api/strategies` (list the 5 strategies + default config) and
  `/crash/api/strategies/performance` (the player's own tracked results).
- `app/games/strategies.py` — new, the staking-plan calculator library.
- `app/models/strategy.py` — new, `StrategyPerformance` model.
- `app/services/mpesa.py` — new. Real Daraja OAuth, STK Push (deposits),
  B2C (withdrawals), and callback parsing. No simulation — this calls
  `sandbox.safaricom.co.ke` / `api.safaricom.co.ke` for real.
- `app/routes/wallet.py` — deposit now actually calls Daraja and creates a
  pending `Transaction`; the callback route matches on `CheckoutRequestID`
  and credits the wallet only once Safaricom confirms. Added `/withdraw`
  (B2C payout, always to the account's own verified phone number — never a
  number typed into a form) and its two callback routes
  (`/mpesa/b2c/result`, `/mpesa/b2c/timeout`).
- `app/models/wallet.py` — `Transaction` gained
  `phone_number, checkout_request_id, merchant_request_id, conversation_id,
  originator_conversation_id, result_desc, updated_at`.
- `config.py` — added the B2C env vars and withdrawal limits.
- Templates: `deposit.html` now asks for the paying phone number;
  `deposit_pending.html` polls `/wallet/deposit/status/<id>` and redirects
  once confirmed; new `withdraw.html`; `overview.html`'s Withdraw button
  now links somewhere.
- `add_mpesa_columns.py` — new. This project boots with `db.create_all()`,
  not Alembic (there's no `migrations/env.py` in this repo despite the
  `migrations/versions/add_strategy_tracking_001.py` file that shipped in
  `files__20_.zip` — that file is inert until you run `flask db init`).
  For a **new** database you don't need this script — `create_all()`
  already includes the new columns. For your **existing deployed**
  database, run this once to `ALTER TABLE transactions ADD COLUMN ...`.

## Environment variables to set on Render

STK Push (deposits) — you already have these from the previous setup:
```
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...
MPESA_SHORTCODE=...          # your paybill/till
MPESA_PASSKEY=...
MPESA_CALLBACK_URL=https://mzizibet.onrender.com/wallet/mpesa/callback
MPESA_ENV=production         # or sandbox while testing
```

B2C (withdrawals) — new, from the Daraja "M-Pesa Express"/B2C API product
on your Safaricom developer app:
```
MPESA_INITIATOR_NAME=...            # the API operator username you set up with Safaricom
MPESA_SECURITY_CREDENTIAL=...       # initiator password encrypted with Safaricom's
                                     # public certificate — generate this offline
                                     # (openssl + Safaricom's cert), never store
                                     # the raw password
MPESA_B2C_SHORTCODE=...             # org shortcode enabled for B2C payouts
MPESA_B2C_RESULT_URL=https://mzizibet.onrender.com/wallet/mpesa/b2c/result
MPESA_B2C_TIMEOUT_URL=https://mzizibet.onrender.com/wallet/mpesa/b2c/timeout
```

Both callback URLs must be public HTTPS endpoints Safaricom can reach —
your Render URL works once deployed; they will not work against `localhost`
without a tunnel (ngrok etc.) during sandbox testing.

## Deploying

```bash
cd /path/to/mzizifeature
# copy every file from this merged folder over your repo, then:
git add -A
git commit -m "feat: enhanced crash leaderboard/strategies + real M-Pesa STK Push & B2C"
git push origin main
```

Then, once only, against your live database:
```bash
python add_mpesa_columns.py
```

## One compliance note, not a code change

The in-house RNG in `mzizicrash_blueprint.py` (HMAC-SHA256 provably-fair
crash points) and the other self-hosted casino games now move real money
through the same wallet as sports betting. You confirmed your BCLB license
covers casino-style gaming as well as sports bookmaking — worth double
checking that your license conditions don't separately require the RNG
itself to be certified by an accredited testing lab (GLI, iTech Labs, etc.),
since that's a common casino-license condition distinct from holding the
operator license itself.
