import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import matplotlib.pyplot as plt
from tabulate import tabulate
import logging
from functools import lru_cache
from typing import Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_plan.log')
    ]
)
logger = logging.getLogger(__name__)

class IWMTradingPlan:
    # Class constants for configuration
    DEFAULT_START_BALANCE = 90.0
    DEFAULT_DAILY_RETURN = 0.10
    DEFAULT_DAYS = 100
    CONTRACT_SIZE = 100
    RISK_PERCENTAGE = 0.1
    MAX_DAILY_LOSS = 0.05  # 5% max daily loss
    MIN_CONTRACTS = 1
    MAX_CONTRACTS = 100

    def __init__(self, start_balance: float = DEFAULT_START_BALANCE,
                 daily_return: float = DEFAULT_DAILY_RETURN,
                 days: int = DEFAULT_DAYS) -> None:
        try:
            self._validate_init_params(start_balance, daily_return, days)
            self.start_balance = start_balance
            self.daily_return = daily_return
            self.days = days
            self.trading_plan = None
            self.current_day = 0
            self.trade_journal: List[Dict] = []
            self.initialize_plan()
            logger.info("Trading plan initialized successfully")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise

    def _validate_init_params(self, start_balance: float, daily_return: float, days: int) -> None:
        """Validate initialization parameters."""
        if not isinstance(start_balance, (int, float)) or start_balance <= 0:
            raise ValueError("Starting balance must be a positive number")
        if not isinstance(daily_return, (int, float)) or daily_return < 0:
            raise ValueError("Daily return must be non-negative")
        if not isinstance(days, int) or days <= 0 or days > 365:
            raise ValueError("Days must be a positive integer up to 365")
        logger.debug(f"Validated init params: balance={start_balance}, return={daily_return}, days={days}")

    def _validate_price(self, price: float) -> bool:
        """Validate price inputs."""
        if not isinstance(price, (int, float)) or price <= 0:
            raise ValueError("Price must be a positive number")
        return True

    def _validate_day(self, day: int) -> bool:
        """Validate trading day."""
        if not isinstance(day, int) or day < 1 or day > self.days:
            raise ValueError(f"Day must be between 1 and {self.days}")
        return True

    def initialize_plan(self) -> None:
        """Initialize the trading plan with technical levels and trading days."""
        try:
            trading_days = self.get_next_trading_days()
            if not trading_days:
                raise ValueError("No trading days available")
            
            ticker = self._get_ticker_data()
            hist = ticker.history(period="6mo")
            if hist.empty:
                raise ValueError("No historical data available")
            
            levels = self.calculate_technical_levels(hist)
            plan_data = []
            current_balance = self.start_balance

            for i, date in enumerate(trading_days):
                contracts = self.calculate_position_size(current_balance, levels.get('atr', 1.0))
                condition = "Bullish" if levels['prev_close'] > levels['50ma'] else "Bearish"

                if condition == "Bullish":
                    direction = "CALL"
                    entry_condition = f"Enter CALL if pre-market high > {levels['r1']:.2f} or opening range high > {levels['pivot']:.2f}"
                    exit_condition = "Exit at 25% profit or 20% loss"
                else:
                    direction = "PUT"
                    entry_condition = f"Enter PUT if pre-market low < {levels['s1']:.2f} or opening range low < {levels['pivot']:.2f}"
                    exit_condition = "Exit at 15% profit or 20% loss"

                plan_data.append([
                    date, i + 1, current_balance, direction, contracts,
                    None, None, None, None, condition,
                    f"Pivot: {levels['pivot']:.2f}, R1: {levels['r1']:.2f}, S1: {levels['s1']:.2f}",
                    entry_condition, exit_condition
                ])

            columns = [
                'Date', 'Day', 'Starting Balance', 'Direction', 'Contracts',
                'Entry Price', 'Exit Price', 'Gain/Loss', 'Ending Balance',
                'Market Condition', 'Key Levels', 'Entry Condition', 'Exit Condition'
            ]
            self.trading_plan = pd.DataFrame(plan_data, columns=columns)
            logger.info(f"Trading plan initialized with {len(trading_days)} days")
        except Exception as e:
            logger.error(f"Failed to initialize trading plan: {str(e)}")
            raise

    @lru_cache(maxsize=32)
    def get_next_trading_days(self) -> List[str]:
        """Get the next trading days from NYSE calendar."""
        try:
            nyse = mcal.get_calendar('NYSE')
            start_date = datetime.now()
            end_date = start_date + timedelta(days=200)
            schedule = nyse.schedule(start_date=start_date, end_date=end_date)
            trading_days = schedule.index[:self.days].strftime('%Y-%m-%d').tolist()
            logger.debug(f"Retrieved {len(trading_days)} trading days")
            return trading_days
        except Exception as e:
            logger.error(f"Failed to get trading days: {str(e)}")
            return []

    @lru_cache(maxsize=8)
    def _get_ticker_data(self) -> yf.Ticker:
        """Get cached yfinance ticker data."""
        try:
            return yf.Ticker("IWM")
        except Exception as e:
            logger.error(f"Failed to get ticker data: {str(e)}")
            raise

    def calculate_technical_levels(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical levels (pivot, support, resistance, moving averages)."""
        try:
            if data.empty:
                raise ValueError("Empty data provided for technical levels")
            
            levels = {
                'prev_close': data['Close'].iloc[-1],
                'pivot': (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3,
                'r1': 2 * ((data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3) - data['Low'].iloc[-1],
                's1': 2 * ((data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3) - data['High'].iloc[-1],
                '20ma': data['Close'].rolling(window=20).mean().iloc[-1],
                '50ma': data['Close'].rolling(window=50).mean().iloc[-1],
                'atr': (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
            }
            logger.debug(f"Calculated technical levels: {levels}")
            return levels
        except Exception as e:
            logger.error(f"Failed to calculate technical levels: {str(e)}")
            return {}

    def calculate_position_size(self, current_balance: float, atr: float) -> int:
        """Calculate position size based on balance and volatility."""
        try:
            self._validate_price(current_balance)
            self._validate_price(atr)
            risk_amount = current_balance * self.RISK_PERCENTAGE
            contracts = int(risk_amount / (atr * self.CONTRACT_SIZE))
            contracts = max(self.MIN_CONTRACTS, min(contracts, self.MAX_CONTRACTS))
            logger.debug(f"Calculated position size: {contracts} contracts")
            return contracts
        except Exception as e:
            logger.error(f"Position sizing error: {str(e)}")
            return self.MIN_CONTRACTS

    def record_trade(self, day: int, entry_price: float, exit_price: float) -> bool:
        """Record a trade and update the plan."""
        try:
            self._validate_day(day)
            self._validate_price(entry_price)
            self._validate_price(exit_price)

            trade_day = self.trading_plan.iloc[day - 1]
            contracts = trade_day['Contracts']
            price_diff = exit_price - entry_price if trade_day['Direction'] == "CALL" else entry_price - exit_price
            gain_loss = price_diff * self.CONTRACT_SIZE * contracts
            ending_balance = trade_day['Starting Balance'] + gain_loss

            # Check daily loss limit
            if ending_balance < trade_day['Starting Balance'] * (1 - self.MAX_DAILY_LOSS):
                logger.warning(f"Trade rejected: Exceeds maximum daily loss limit")
                return False

            trade_record = {
                'Date': trade_day['Date'],
                'Day': trade_day['Day'],
                'Direction': trade_day['Direction'],
                'Contracts': contracts,
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'Gain/Loss': gain_loss,
                'Ending Balance': ending_balance,
                'Starting Balance': trade_day['Starting Balance']
            }
            self.trade_journal.append(trade_record)

            self.trading_plan.at[day - 1, 'Entry Price'] = entry_price
            self.trading_plan.at[day - 1, 'Exit Price'] = exit_price
            self.trading_plan.at[day - 1, 'Gain/Loss'] = gain_loss
            self.trading_plan.at[day - 1, 'Ending Balance'] = ending_balance

            if day < self.days:
                self.trading_plan.at[day, 'Starting Balance'] = ending_balance

            logger.info(f"Trade recorded for Day {day}: Gain/Loss: ${gain_loss:.2f}, New Balance: ${ending_balance:.2f}")
            self.current_day = day
            return True
        except Exception as e:
            logger.error(f"Failed to record trade: {str(e)}")
            return False

    def get_daily_plan(self, day: Optional[int] = None) -> Optional[Dict]:
        """Get the trading plan for a specific day."""
        try:
            if day is None:
                day = self.current_day + 1
            self._validate_day(day)
            plan = self.trading_plan.iloc[day - 1].to_dict()
            logger.debug(f"Retrieved plan for day {day}")
            return plan
        except Exception as e:
            logger.error(f"Failed to get daily plan: {str(e)}")
            return None

    def update_daily_plan(self, starting_balance: float, market_condition: str, direction: str,
                         contracts: int, key_levels: str, entry_condition: str,
                         exit_condition: str) -> bool:
        """Update today's trading plan with new values."""
        try:
            day = self.current_day + 1
            self._validate_day(day)
            self._validate_price(starting_balance)
            if market_condition not in ["Bullish", "Bearish"]:
                raise ValueError("Market condition must be 'Bullish' or 'Bearish'")
            if direction not in ["CALL", "PUT"]:
                raise ValueError("Direction must be 'CALL' or 'PUT'")
            if not isinstance(contracts, int) or contracts < self.MIN_CONTRACTS or contracts > self.MAX_CONTRACTS:
                raise ValueError(f"Contracts must be between {self.MIN_CONTRACTS} and {self.MAX_CONTRACTS}")

            self.trading_plan.at[day - 1, 'Starting Balance'] = starting_balance
            self.trading_plan.at[day - 1, 'Market Condition'] = market_condition
            self.trading_plan.at[day - 1, 'Direction'] = direction
            self.trading_plan.at[day - 1, 'Contracts'] = contracts
            self.trading_plan.at[day - 1, 'Key Levels'] = key_levels
            self.trading_plan.at[day - 1, 'Entry Condition'] = entry_condition
            self.trading_plan.at[day - 1, 'Exit Condition'] = exit_condition

            logger.info(f"Plan updated for Day {day}")
            return True
        except Exception as e:
            logger.error(f"Failed to update daily plan: {str(e)}")
            return False

    def get_market_analysis(self) -> Dict[str, Union[float, str, Dict]]:
        """Get current market analysis with technical levels."""
        try:
            ticker = self._get_ticker_data()
            hist = ticker.history(period="1mo")
            if hist.empty:
                raise ValueError("No historical data available")
            
            levels = self.calculate_technical_levels(hist)
            current_data = ticker.history(period="1d")
            if current_data.empty:
                raise ValueError("No current price data available")
            
            current_price = current_data['Close'].iloc[-1]
            condition = "Bullish" if current_price > levels.get('50ma', 0) else "Bearish"

            analysis = {
                'Current Price': current_price,
                'Market Condition': condition,
                'Key Levels': levels,
                'Recommendation': "BUY CALLS" if condition == "Bullish" else "BUY PUTS"
            }
            logger.debug(f"Market analysis: {analysis}")
            return analysis
        except Exception as e:
            logger.error(f"Market analysis failed: {str(e)}")
            return {
                'Current Price': 0.0,
                'Market Condition': "Neutral",
                'Key Levels': {},
                'Recommendation': "No recommendation - data unavailable",
                'Error': str(e)
            }

    def plot_performance(self) -> None:
        """Plot account balance over time."""
        try:
            if not self.trade_journal:
                logger.warning("No trades recorded for plotting")
                print("No trades recorded yet")
                return

            days = [t['Day'] for t in self.trade_journal]
            balances = [t['Ending Balance'] for t in self.trade_journal]

            plt.figure(figsize=(12, 6))
            plt.plot(days, balances, marker='o', linestyle='-', color='b')
            plt.title('Trading Account Performance')
            plt.xlabel('Trading Days')
            plt.ylabel('Account Balance ($)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
            logger.info("Performance plot generated")
        except Exception as e:
            logger.error(f"Failed to plot performance: {str(e)}")

    def show_summary(self) -> None:
        """Display trading performance summary."""
        try:
            if not self.trade_journal:
                logger.warning("No trades recorded for summary")
                print("No trades recorded yet")
                return

            start_balance = self.trade_journal[0]['Starting Balance']
            current_balance = self.trade_journal[-1]['Ending Balance']
            total_gain = current_balance - start_balance
            growth_percent = (total_gain / start_balance) * 100

            wins = sum(1 for t in self.trade_journal if t['Gain/Loss'] > 0)
            losses = sum(1 for t in self.trade_journal if t['Gain/Loss'] < 0)
            win_rate = (wins / len(self.trade_journal)) * 100

            print("\n" + "=" * 50)
            print("TRADING PERFORMANCE SUMMARY")
            print("=" * 50)
            print(f"Starting Balance: ${start_balance:.2f}")
            print(f"Current Balance: ${current_balance:.2f}")
            print(f"Total Gain/Loss: ${total_gain:.2f} ({growth_percent:.2f}%)")
            print(f"Trades Completed: {len(self.trade_journal)}")
            print(f"Win Rate: {win_rate:.2f}% ({wins} wins, {losses} losses)")
            print("=" * 50)

            if len(self.trade_journal) > 0:
                print("\nLAST 5 TRADES:")
                recent_trades = self.trade_journal[-5:] if len(self.trade_journal) > 5 else self.trade_journal
                print(tabulate(
                    pd.DataFrame(recent_trades)[['Date', 'Day', 'Direction', 'Contracts',
                                                'Entry Price', 'Exit Price', 'Gain/Loss']],
                    headers='keys', tablefmt='psql', showindex=False
                ))
            logger.info("Performance summary generated")
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
