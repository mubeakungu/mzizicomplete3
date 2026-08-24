"""Strategy performance tracking.

Populated when a player opts into one of the staking-plan strategies in
app/games/strategies.py while playing a real-money round. This is a
record-keeping table only — strategies never place bets automatically;
the player still confirms every stake and every cashout themselves.
"""
from datetime import datetime
from app.extensions import db


class StrategyPerformance(db.Model):
    __tablename__ = "strategy_performance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # e.g. "crash"
    strategy_name = db.Column(db.String(50), nullable=False)

    total_bets = db.Column(db.Integer, default=0)
    total_wagered = db.Column(db.Numeric(10, 2), default=0)
    total_won = db.Column(db.Numeric(10, 2), default=0)
    total_lost = db.Column(db.Numeric(10, 2), default=0)
    win_count = db.Column(db.Integer, default=0)
    loss_count = db.Column(db.Integer, default=0)
    best_profit = db.Column(db.Numeric(10, 2), default=0)
    worst_loss = db.Column(db.Numeric(10, 2), default=0)
    average_multiplier = db.Column(db.Float, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref="strategy_performances")

    __table_args__ = (
        db.Index("ix_strategy_performance_user_id_game_type", "user_id", "game_type"),
        db.Index("ix_strategy_performance_strategy_name", "strategy_name"),
    )

    def record_result(self, wagered, won, payout, multiplier=None):
        """Update running totals after one resolved bet."""
        wagered = wagered or 0
        payout = payout or 0
        profit = payout - wagered

        self.total_bets = (self.total_bets or 0) + 1
        self.total_wagered = (self.total_wagered or 0) + wagered

        if won:
            self.win_count = (self.win_count or 0) + 1
            self.total_won = (self.total_won or 0) + payout
            if profit > (self.best_profit or 0):
                self.best_profit = profit
        else:
            self.loss_count = (self.loss_count or 0) + 1
            self.total_lost = (self.total_lost or 0) + wagered
            if -wagered < (self.worst_loss or 0) or self.worst_loss in (None, 0):
                self.worst_loss = -wagered

        if multiplier is not None:
            n = self.total_bets or 1
            prev_avg = self.average_multiplier or 0
            self.average_multiplier = prev_avg + (float(multiplier) - prev_avg) / n

    def to_dict(self):
        return {
            "game_type": self.game_type,
            "strategy_name": self.strategy_name,
            "total_bets": self.total_bets,
            "total_wagered": float(self.total_wagered or 0),
            "total_won": float(self.total_won or 0),
            "total_lost": float(self.total_lost or 0),
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "best_profit": float(self.best_profit or 0),
            "worst_loss": float(self.worst_loss or 0),
            "average_multiplier": round(self.average_multiplier or 0, 2),
        }
