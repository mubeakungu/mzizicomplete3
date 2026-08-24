"""
games_static blueprint
──────────────────────
Serves the built React games SPA (Crash, Plinko, Mines, Dino) at /games/*.

HOW TO BUILD:
  cd rebrand/          # the React source directory
  npm install
  npm run build        # outputs to app/static/games/ via vite.config.js

After building you'll have:
  app/static/games/index.html
  app/static/games/assets/...

Every /games/* URL that isn't a real static file falls through to index.html
so React Router can handle client-side routing (/games/crash, /games/plinko, etc.)
"""

import os
from flask import Blueprint, send_from_directory, current_app

games_static_bp = Blueprint("games_static", __name__)


def _games_dist():
    return os.path.join(current_app.static_folder, "games")


@games_static_bp.route("/games/")
@games_static_bp.route("/games/<path:subpath>")
def serve_games(subpath=""):
    dist = _games_dist()
    # Serve real files (JS/CSS/assets) directly
    if subpath:
        candidate = os.path.join(dist, subpath)
        if os.path.isfile(candidate):
            return send_from_directory(dist, subpath)
    # Everything else → index.html (React Router takes over)
    return send_from_directory(dist, "index.html")
