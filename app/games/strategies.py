"""
Betting Strategies Module
Extracted and adapted from Aviator-Automated-Betika-Bot

Provides configurable betting strategies for crash/aviator games:
- Conservative: Low risk, steady gains
- Moderate: Balanced risk/reward
- Aggressive: High risk, high potential reward
- Kelly Criterion: Mathematically optimal bet sizing
- Martingale: Double bet after loss (high variance)

Usage:
    strategy = BettingStrategy.get_strategy("moderate")
    next_bet = strategy.calculate_next_bet(current_balance, last_result)
"""

from decimal import Decimal
from enum import Enum
import math


class StrategyType(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    KELLY = "kelly"
    MARTINGALE = "martingale"


class BettingStrategy:
    """Base class for betting strategies"""
    
    def __init__(self, config):
        self.initial_bet = Decimal(str(config.get("initial_bet", 100)))
        self.min_bet = Decimal(str(config.get("min_bet", 10)))
        self.max_bet = Decimal(str(config.get("max_bet", 10000)))
        self.target_multiplier = Decimal(str(config.get("target_multiplier", 1.5)))
        self.stop_loss = Decimal(str(config.get("stop_loss", -1000)))
        self.take_profit = Decimal(str(config.get("take_profit", 5000)))
        self.martingale_multiplier = Decimal(str(config.get("martingale_multiplier", 1.5)))
        
        # Track state
        self.total_profit = Decimal("0")
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.bet_sequence = []
        self.results = []
    
    def calculate_next_bet(self, current_balance, last_result=None):
        """
        Calculate next bet amount
        
        Args:
            current_balance: Current wallet balance (Decimal)
            last_result: {"won": bool, "payout": Decimal, "loss": Decimal}
        
        Returns:
            Decimal: Bet amount
        """
        raise NotImplementedError
    
    def on_win(self, payout):
        """Track win"""
        self.consecutive_wins += 1
        self.consecutive_losses = 0
        self.total_profit += payout - self.bet_sequence[-1] if self.bet_sequence else Decimal("0")
        self.results.append({"type": "win", "payout": payout})
    
    def on_loss(self, loss_amount):
        """Track loss"""
        self.consecutive_losses += 1
        self.consecutive_wins = 0
        self.total_profit -= loss_amount
        self.results.append({"type": "loss", "loss": loss_amount})
    
    def reset(self):
        """Reset strategy state"""
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.bet_sequence = []
        self.total_profit = Decimal("0")


class ConservativeStrategy(BettingStrategy):
    """
    Conservative Strategy
    - Low risk, steady gains
    - Targets low multipliers (1.2x - 1.5x)
    - Gradual bet increases
    - Tight stop-loss
    
    Config:
        initial_bet: 100 (default)
        min_bet: 50
        max_bet: 500
        target_multiplier: 1.5
        stop_loss: -1000
        take_profit: 5000
        martingale_multiplier: 1.5
    """
    
    @staticmethod
    def default_config():
        return {
            "initial_bet": 100,
            "min_bet": 50,
            "max_bet": 500,
            "target_multiplier": 1.5,
            "stop_loss": -1000,
            "take_profit": 5000,
            "martingale_multiplier": 1.5
        }
    
    def calculate_next_bet(self, current_balance, last_result=None):
        """Conservative betting: increase slowly after wins, reset after losses"""
        
        # Check stop-loss
        if self.total_profit <= self.stop_loss:
            return Decimal("0")  # Signal to stop betting
        
        # Check take-profit
        if self.total_profit >= self.take_profit:
            return Decimal("0")  # Signal to stop (target reached)
        
        if last_result is None:
            # First bet
            bet = self.initial_bet
        elif last_result["won"]:
            self.on_win(last_result["payout"])
            # After win: increase bet slightly (1.1x)
            last_bet = self.bet_sequence[-1] if self.bet_sequence else self.initial_bet
            bet = min(last_bet * Decimal("1.1"), self.max_bet)
        else:
            self.on_loss(last_result["loss"])
            # After loss: reset to initial bet
            bet = self.initial_bet
        
        # Ensure within bounds
        bet = max(self.min_bet, min(bet, self.max_bet))
        bet = min(bet, current_balance)  # Don't exceed balance
        
        self.bet_sequence.append(bet)
        return bet


class ModerateStrategy(BettingStrategy):
    """
    Moderate Strategy
    - Balanced risk/reward
    - Targets medium multipliers (1.8x - 2.2x)
    - Moderate bet increases
    - Flexible stop-loss
    
    Config:
        initial_bet: 200
        min_bet: 100
        max_bet: 1500
        target_multiplier: 2.0
        stop_loss: -2000
        take_profit: 10000
        martingale_multiplier: 1.8
    """
    
    @staticmethod
    def default_config():
        return {
            "initial_bet": 200,
            "min_bet": 100,
            "max_bet": 1500,
            "target_multiplier": 2.0,
            "stop_loss": -2000,
            "take_profit": 10000,
            "martingale_multiplier": 1.8
        }
    
    def calculate_next_bet(self, current_balance, last_result=None):
        """Moderate betting: increase after wins, apply martingale after losses"""
        
        # Check stop-loss
        if self.total_profit <= self.stop_loss:
            return Decimal("0")
        
        # Check take-profit
        if self.total_profit >= self.take_profit:
            return Decimal("0")
        
        if last_result is None:
            # First bet
            bet = self.initial_bet
        elif last_result["won"]:
            self.on_win(last_result["payout"])
            # After win: increase bet by 20%
            last_bet = self.bet_sequence[-1] if self.bet_sequence else self.initial_bet
            bet = last_bet * Decimal("1.2")
        else:
            self.on_loss(last_result["loss"])
            # After loss: apply martingale (increase for recovery)
            if self.consecutive_losses > 0:
                last_bet = self.bet_sequence[-1] if self.bet_sequence else self.initial_bet
                bet = last_bet * self.martingale_multiplier
            else:
                bet = self.initial_bet
        
        # Ensure within bounds
        bet = max(self.min_bet, min(bet, self.max_bet))
        bet = min(bet, current_balance)
        
        self.bet_sequence.append(bet)
        return bet


class AggressiveStrategy(BettingStrategy):
    """
    Aggressive Strategy
    - High risk, high reward
    - Targets high multipliers (2.5x - 3.5x)
    - Rapid bet increases
    - Wide stop-loss
    
    Config:
        initial_bet: 500
        min_bet: 200
        max_bet: 5000
        target_multiplier: 3.0
        stop_loss: -5000
        take_profit: 25000
        martingale_multiplier: 2.0
    """
    
    @staticmethod
    def default_config():
        return {
            "initial_bet": 500,
            "min_bet": 200,
            "max_bet": 5000,
            "target_multiplier": 3.0,
            "stop_loss": -5000,
            "take_profit": 25000,
            "martingale_multiplier": 2.0
        }
    
    def calculate_next_bet(self, current_balance, last_result=None):
        """Aggressive betting: rapid increases on wins, aggressive martingale on losses"""
        
        # Check stop-loss
        if self.total_profit <= self.stop_loss:
            return Decimal("0")
        
        # Check take-profit
        if self.total_profit >= self.take_profit:
            return Decimal("0")
        
        if last_result is None:
            # First bet
            bet = self.initial_bet
        elif last_result["won"]:
            self.on_win(last_result["payout"])
            # After win: increase bet by 40%
            last_bet = self.bet_sequence[-1] if self.bet_sequence else self.initial_bet
            bet = last_bet * Decimal("1.4")
        else:
            self.on_loss(last_result["loss"])
            # After loss: apply aggressive martingale
            if self.consecutive_losses > 0:
                last_bet = self.bet_sequence[-1] if self.bet_sequence else self.initial_bet
                bet = last_bet * self.martingale_multiplier
            else:
                bet = self.initial_bet
        
        # Ensure within bounds
        bet = max(self.min_bet, min(bet, self.max_bet))
        bet = min(bet, current_balance)
        
        self.bet_sequence.append(bet)
        return bet


class KellyCriterionStrategy(BettingStrategy):
    """
    Kelly Criterion Strategy
    - Mathematically optimal bet sizing
    - Formula: f = (bp - q) / b
      where: f = fraction of bankroll
             b = odds (multiplier - 1)
             p = probability of win
             q = probability of loss (1-p)
    
    - Conservative variant uses 50% of Kelly value (half-kelly)
    - Requires historical win rate data
    
    Config:
        initial_bet: 100
        min_bet: 50
        max_bet: 1000
        win_rate: 0.55 (55% wins assumed)
        kelly_fraction: 0.25 (quarter-kelly for safety)
    """
    
    @staticmethod
    def default_config():
        return {
            "initial_bet": 100,
            "min_bet": 50,
            "max_bet": 1000,
            "target_multiplier": 2.0,
            "win_rate": Decimal("0.55"),  # Assume 55% win rate
            "kelly_fraction": Decimal("0.25"),  # Quarter-kelly (conservative)
            "stop_loss": -2000,
            "take_profit": 10000
        }
    
    def __init__(self, config):
        super().__init__(config)
        self.win_rate = Decimal(str(config.get("win_rate", "0.55")))
        self.kelly_fraction = Decimal(str(config.get("kelly_fraction", "0.25")))
    
    def calculate_next_bet(self, current_balance, last_result=None):
        """Kelly criterion: optimal bet sizing based on win probability"""
        
        # Check stop-loss and take-profit
        if self.total_profit <= self.stop_loss:
            return Decimal("0")
        if self.total_profit >= self.take_profit:
            return Decimal("0")
        
        # Calculate actual win rate from history
        if len(self.results) > 20:
            wins = len([r for r in self.results[-20:] if r["type"] == "win"])
            actual_win_rate = Decimal(wins) / Decimal(20)
        else:
            actual_win_rate = self.win_rate
        
        # Kelly formula: f = (bp - q) / b
        # Assume average multiplier is target_multiplier
        b = self.target_multiplier - 1  # odds
        p = actual_win_rate
        q = 1 - p
        
        if b > 0:
            kelly_fraction = (b * p - q) / b
            # Apply kelly_fraction as safety factor
            kelly_fraction = kelly_fraction * self.kelly_fraction
            kelly_fraction = max(Decimal("0"), min(kelly_fraction, Decimal("1")))
        else:
            kelly_fraction = Decimal("0.01")
        
        # Bet is kelly_fraction of bankroll
        bet = current_balance * kelly_fraction
        
        # Ensure within bounds
        bet = max(self.min_bet, min(bet, self.max_bet))
        bet = min(bet, current_balance)
        
        self.bet_sequence.append(bet)
        return bet


class MartingaleStrategy(BettingStrategy):
    """
    Martingale Strategy
    - Double bet after each loss
    - Reset after win
    - Classic progression system
    - High risk of rapid bankroll depletion
    
    Config:
        initial_bet: 100
        min_bet: 50
        max_bet: 10000
        martingale_multiplier: 2.0 (double each time)
        max_sequence_length: 5 (stop doubling after 5 losses)
    """
    
    @staticmethod
    def default_config():
        return {
            "initial_bet": 100,
            "min_bet": 50,
            "max_bet": 10000,
            "target_multiplier": 1.5,
            "martingale_multiplier": 2.0,
            "max_sequence_length": 5,
            "stop_loss": -5000,
            "take_profit": 10000
        }
    
    def __init__(self, config):
        super().__init__(config)
        self.max_sequence_length = config.get("max_sequence_length", 5)
    
    def calculate_next_bet(self, current_balance, last_result=None):
        """Martingale: double bet after loss, reset after win"""
        
        # Check stop-loss
        if self.total_profit <= self.stop_loss:
            return Decimal("0")
        
        # Check take-profit
        if self.total_profit >= self.take_profit:
            return Decimal("0")
        
        if last_result is None:
            # First bet
            bet = self.initial_bet
        elif last_result["won"]:
            self.on_win(last_result["payout"])
            # After win: reset to initial
            bet = self.initial_bet
        else:
            self.on_loss(last_result["loss"])
            # After loss: double the bet (up to max sequence)
            if self.consecutive_losses < self.max_sequence_length:
                last_bet = self.bet_sequence[-1] if self.bet_sequence else self.initial_bet
                bet = last_bet * self.martingale_multiplier
            else:
                # Too many losses, reset
                bet = self.initial_bet
        
        # Ensure within bounds
        bet = max(self.min_bet, min(bet, self.max_bet))
        bet = min(bet, current_balance)
        
        self.bet_sequence.append(bet)
        return bet


class StrategyFactory:
    """Factory for creating betting strategies"""
    
    STRATEGIES = {
        StrategyType.CONSERVATIVE: ConservativeStrategy,
        StrategyType.MODERATE: ModerateStrategy,
        StrategyType.AGGRESSIVE: AggressiveStrategy,
        StrategyType.KELLY: KellyCriterionStrategy,
        StrategyType.MARTINGALE: MartingaleStrategy,
    }
    
    @classmethod
    def create(cls, strategy_type, config=None):
        """
        Create a strategy instance
        
        Args:
            strategy_type: StrategyType enum or string
            config: Optional custom config dict
        
        Returns:
            BettingStrategy instance
        """
        if isinstance(strategy_type, str):
            strategy_type = StrategyType(strategy_type.lower())
        
        strategy_class = cls.STRATEGIES.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        if config is None:
            config = strategy_class.default_config()
        
        return strategy_class(config)
    
    @classmethod
    def get_default_config(cls, strategy_type):
        """Get default config for a strategy"""
        if isinstance(strategy_type, str):
            strategy_type = StrategyType(strategy_type.lower())
        
        strategy_class = cls.STRATEGIES.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        return strategy_class.default_config()
    
    @classmethod
    def list_strategies(cls):
        """List all available strategies"""
        return list(cls.STRATEGIES.keys())


# Convenience functions
def get_strategy(strategy_name, config=None):
    """Get a strategy by name"""
    return StrategyFactory.create(strategy_name, config)


def get_strategy_config(strategy_name):
    """Get default config for a strategy"""
    return StrategyFactory.get_default_config(strategy_name)


# Example usage
if __name__ == "__main__":
    # Create moderate strategy
    strategy = StrategyFactory.create(StrategyType.MODERATE)
    
    # First bet
    balance = Decimal("10000")
    bet1 = strategy.calculate_next_bet(balance)
    print(f"First bet: {bet1}")
    
    # After win
    balance += bet1 * Decimal("2")  # Won at 2x
    result_win = {"won": True, "payout": bet1 * Decimal("2")}
    bet2 = strategy.calculate_next_bet(balance, result_win)
    print(f"After win: {bet2}")
    
    # After loss
    balance -= bet2
    result_loss = {"won": False, "loss": bet2}
    bet3 = strategy.calculate_next_bet(balance, result_loss)
    print(f"After loss: {bet3}")
    
    # List all strategies
    print("\nAvailable strategies:")
    for strat in StrategyFactory.list_strategies():
        print(f"  - {strat.value}")
