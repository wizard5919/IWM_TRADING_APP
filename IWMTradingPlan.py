
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import matplotlib.pyplot as plt
from tabulate import tabulate

class IWMTradingPlan:
    def __init__(self, start_balance=90, daily_return=0.10, days=100):
        self.start_balance = start_balance
        self.daily_return = daily_return
        self.days = days
        self.trading_plan = None
        self.current_day = 0
        self.trade_journal = []
        self.initialize_plan()

    def initialize_plan(self):
        trading_days = self.get_next_trading_days()
        ticker = yf.Ticker("IWM")
        hist = ticker.history(period="6mo")
        levels = self.calculate_technical_levels(hist)

        plan_data = []
        current_balance = self.start_balance

        for i, date in enumerate(trading_days):
            contracts = f"max(1, int({current_balance} * 0.1 / 10))"
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

            current_balance = f"Ending balance from day {i+1}"

        columns = [
            'Date', 'Day', 'Starting Balance', 'Direction', 'Contracts',
            'Entry Price', 'Exit Price', 'Gain/Loss', 'Ending Balance',
            'Market Condition', 'Key Levels', 'Entry Condition', 'Exit Condition'
        ]
        self.trading_plan = pd.DataFrame(plan_data, columns=columns)

    def get_next_trading_days(self):
        nyse = mcal.get_calendar('NYSE')
        start_date = datetime.now()
        end_date = start_date + timedelta(days=200)
        schedule = nyse.schedule(start_date=start_date, end_date=end_date)
        return schedule.index[:self.days].strftime('%Y-%m-%d').tolist()

    def calculate_technical_levels(self, data):
        return {
            'prev_close': data['Close'].iloc[-1],
            'pivot': (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3,
            'r1': 2 * ((data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3) - data['Low'].iloc[-1],
            's1': 2 * ((data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3) - data['High'].iloc[-1],
            '20ma': data['Close'].rolling(window=20).mean().iloc[-1],
            '50ma': data['Close'].rolling(window=50).mean().iloc[-1],
            'atr': (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
        }

    def record_trade(self, day, entry_price, exit_price):
        if day < 1 or day > self.days:
            print(f"Invalid day. Must be between 1 and {self.days}")
            return

        trade_day = self.trading_plan.iloc[day - 1]
        contracts = max(1, int(trade_day['Starting Balance'] * 0.1 / 10))
        price_diff = exit_price - entry_price
        gain_loss = price_diff * 100 * contracts
        ending_balance = trade_day['Starting Balance'] + gain_loss

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

        print(f"Trade recorded for Day {day}:")
        print(f"Gain/Loss: ${gain_loss:.2f} | New Balance: ${ending_balance:.2f}")
        self.current_day = day

    def get_daily_plan(self, day=None):
        if day is None:
            day = self.current_day + 1

        if day < 1 or day > self.days:
            print(f"Invalid day. Must be between 1 and {self.days}")
            return None

        return self.trading_plan.iloc[day - 1]
        
    def update_daily_plan(self, starting_balance, market_condition, direction, 
                      contracts, key_levels, entry_condition, exit_condition):
    """Update today's trading plan with new values"""
    day = self.current_day + 1
    
    if day < 1 or day > self.days:
        print(f"Invalid day. Must be between 1 and {self.days}")
        return
    
    # Update all editable fields
    self.trading_plan.at[day - 1, 'Starting Balance'] = starting_balance
    self.trading_plan.at[day - 1, 'Market Condition'] = market_condition
    self.trading_plan.at[day - 1, 'Direction'] = direction
    self.trading_plan.at[day - 1, 'Contracts'] = contracts
    self.trading_plan.at[day - 1, 'Key Levels'] = key_levels
    self.trading_plan.at[day - 1, 'Entry Condition'] = entry_condition
    self.trading_plan.at[day - 1, 'Exit Condition'] = exit_condition
    
    print(f"Plan updated for Day {day}")

    def get_market_analysis(self):
        ticker = yf.Ticker("IWM")
        hist = ticker.history(period="1mo")
        levels = self.calculate_technical_levels(hist)
        current_data = ticker.history(period="1d")
        current_price = current_data['Close'].iloc[-1]
        condition = "Bullish" if current_price > levels['50ma'] else "Bearish"

        return {
            'Current Price': current_price,
            'Market Condition': condition,
            'Key Levels': levels,
            'Recommendation': "BUY CALLS" if condition == "Bullish" else "BUY PUTS"
        }

    def plot_performance(self):
        if not self.trade_journal:
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

    def show_summary(self):
        if not self.trade_journal:
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



