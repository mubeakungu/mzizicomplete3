# =========================================================================
# MODIFICATION TO: app/__init__.py
# PURPOSE: Show landing page for unauthenticated users
# =========================================================================

# STEP 1: Update imports (around line 12)
# =========================================================================
# CHANGE FROM:
from flask import Flask, redirect, url_for

# CHANGE TO:
from flask import Flask, redirect, url_for, render_template


# STEP 2: Update the index route (around line 288-290)
# =========================================================================
# CHANGE FROM:
@app.route("/")
def index():
    return redirect(url_for("casino.lobby"))


# CHANGE TO:
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("casino.lobby"))
    return render_template("landing.html")


# =========================================================================
# NO OTHER CHANGES NEEDED!
# =========================================================================
# The landing.html template is already created and contains all necessary
# styles and HTML. The rest of the application remains unchanged.
#
# TESTING:
# 1. Log out completely (clear session/cookies if needed)
# 2. Visit http://localhost:5000 or your deployed URL
# 3. You should see the landing page instead of being redirected
# 4. Log in via the "Sign in" button
# 5. Verify you're redirected to the casino lobby
# 6. Log out and return to home - landing page appears again
# =========================================================================
