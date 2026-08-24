"""Single source of truth for how catalog games are launched.

The catalog slug is the stable public identifier. Every self-hosted game has
exactly one canonical template/route here. The casino lobby must not contain
another implementation of a game in JavaScript.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GameDefinition:
    slug: str
    template: Optional[str] = None
    route: Optional[str] = None
    kind: str = "self_hosted"  # self_hosted | redirect | provider
    namespace: Optional[str] = None


GAME_REGISTRY = {
    # Real-time games: their dedicated blueprints own the game loop + API.
    "mzizicrash": GameDefinition(
        slug="mzizicrash", route="/crash/", kind="redirect", namespace="/crash"
    ),
    "aviatormzizi": GameDefinition(
        slug="aviatormzizi", route="/aviator-mzizi/", kind="redirect", namespace="/aviator-mzizi"
    ),
    "hilocard": GameDefinition(
        slug="hilocard", route="/hi-lo-card/", kind="redirect", namespace="/hi-lo-card"
    ),

    # Rebrand React games — served by games_static blueprint at /games/*
    # NOTE: the rebrand's WalletContext (rebrand/src/context/WalletContext.jsx)
    # is a browser-localStorage demo balance, NOT connected to the real
    # Flask wallet/DB. Anything routed here is free-play only until a real
    # backend (server-side RNG + /api/casino-style settle-round against the
    # user's actual Wallet row) is built for it. Do not treat wins/losses
    # here as real money.
    # JetX is replaced by the new Crash game from the rebrand (demo only)
    "jetx": GameDefinition(
        slug="jetx", route="/games/crash", kind="redirect"
    ),
    "dino": GameDefinition(
        slug="dino", route="/games/dino", kind="redirect"
    ),

    # HTTP/API games: their dedicated templates are the canonical UI and
    # /api/casino is the canonical settlement API.
    "dice": GameDefinition(slug="dice", template="games/dice.html"),
    "european-roulette": GameDefinition(
        slug="european-roulette", template="games/european-roulette.html"
    ),
    "slots": GameDefinition(slug="slots", template="games/slots.html"),
    "mines": GameDefinition(slug="mines", template="games/mines.html"),

    # Real, wallet-integrated backend — own blueprint, own DB models.
    # (Previously mispointed at the fake-wallet /games/plinko rebrand demo.)
    "plinkomzizi": GameDefinition(
        slug="plinkomzizi", route="/plinko-mzizi/", kind="redirect", namespace="/plinko-mzizi"
    ),

    # Placeholder — game engine not yet built.
    "coin-flip": GameDefinition(slug="coin-flip", kind="coming_soon"),
}


def get_game_definition(slug: str) -> Optional[GameDefinition]:
    return GAME_REGISTRY.get(slug)


def is_canonical_game(slug: str) -> bool:
    return slug in GAME_REGISTRY
