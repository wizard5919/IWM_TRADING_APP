import streamlit as st
from IWMTradingPlan import IWMTradingPlan
import pandas as pd
import matplotlib.pyplot as plt
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_app.log')
    ]
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="IWM 0DTE Trading App", layout="centered")
st.title("📈 IWM 0DTE Trading Plan & Tracker")

# Initialize session state
if 'plan' not in st.session_state:
    try:
        st.session_state.plan = IWMTradingPlan()
        logger.info("IWMTradingPlan initialized in session state")
    except Exception as e:
        st.error(f"Failed to initialize trading plan: {str(e)}")
        logger.error(f"Initialization error: {str(e)}")
        st.stop()

plan = st.session_state.plan

# Sidebar navigation
page = st.sidebar.radio("Go to", ["📅 Today's Plan", "🧮 Record a Trade", "📊 Performance Summary"])

if page == "📅 Today's Plan":
    st.header("📅 Today's Trading Plan")
    try:
        day_plan = plan.get_daily_plan()
        if day_plan is None:
            st.error("Unable to retrieve today's plan. Please check logs.")
            logger.error("Failed to retrieve daily plan")
            st.stop()
        
        # Use columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Date:** {day_plan['Date']}")
            
            # Editable starting balance
            starting_balance = st.number_input(
                "**Starting Balance ($)**", 
                value=float(day_plan['Starting Balance']),
                min_value=1.0,
                step=1.0,
                format="%.2f"
            )
            
            # Editable market condition
            market_condition = st.selectbox(
                "**Market Condition**", 
                ["Bullish", "Bearish"], 
                index=0 if day_plan['Market Condition'] == "Bullish" else 1
            )
            
            # Editable direction
            direction = st.selectbox(
                "**Direction**", 
                ["CALL", "PUT"], 
                index=0 if day_plan['Direction'] == "CALL" else 1
            )
            
            # Editable contracts
            contracts = st.number_input(
                "**Contracts**", 
                value=int(day_plan['Contracts']), 
                min_value=plan.MIN_CONTRACTS,
                max_value=plan.MAX_CONTRACTS,
                step=1
            )
        
        with col2:
            # Editable key levels
            st.write("**Key Levels**")
            levels_str = day_plan['Key Levels']
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", levels_str)
            if len(numbers) >= 3:
                pivot = float(numbers[0])
                r1 = float(numbers[1])
                s1 = float(numbers[2])
            else:
                pivot = r1 = s1 = 0.0
                st.warning("Invalid key levels format. Using defaults.")
                logger.warning(f"Invalid key levels format: {levels_str}")
            
            pivot = st.number_input("Pivot", value=pivot, min_value=0.0, step=0.01, format="%.2f")
            r1 = st.number_input("R1", value=r1, min_value=0.0, step=0.01, format="%.2f")
            s1 = st.number_input("S1", value=s1, min_value=0.0, step=0.01, format="%.2f")
            
            updated_levels = f"Pivot: {pivot:.2f}, R1: {r1:.2f}, S1: {s1:.2f}"
        
        # Editable entry condition
        entry_condition = day_plan['Entry Condition']
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", entry_condition)
        if len(numbers) >= 2:
            threshold1 = float(numbers[0])
            threshold2 = float(numbers[1])
        else:
            threshold1 = threshold2 = 0.0
            st.warning("Invalid entry condition format. Using defaults.")
            logger.warning(f"Invalid entry condition format: {entry_condition}")
        
        st.write("**Entry Condition**")
        col3, col4 = st.columns(2)
        with col3:
            new_threshold1 = st.number_input("Threshold 1", value=threshold1, min_value=0.0, step=0.01, format="%.2f")
        with col4:
            new_threshold2 = st.number_input("Threshold 2", value=threshold2, min_value=0.0, step=0.01, format="%.2f")
        
        updated_entry = (f"Enter {direction} if pre-market {'high' if direction == 'CALL' else 'low'} > {new_threshold1:.2f} "
                        f"or opening range {'high' if direction == 'CALL' else 'low'} > {new_threshold2:.2f}")
        
        # Editable exit condition
        exit_condition = day_plan['Exit Condition']
        numbers = re.findall(r"\d+", exit_condition)
        if len(numbers) >= 2:
            profit_target = int(numbers[0])
            stop_loss = int(numbers[1])
        else:
            profit_target = 25
            stop_loss = 20
            st.warning("Invalid exit condition format. Using defaults.")
            logger.warning(f"Invalid exit condition format: {exit_condition}")
        
        st.write("**Exit Condition**")
        col5, col6 = st.columns(2)
        with col5:
            new_profit_target = st.number_input("Profit Target (%)", value=profit_target, min_value=1, max_value=100, step=1)
        with col6:
            new_stop_loss = st.number_input("Stop Loss (%)", value=stop_loss, min_value=1, max_value=100, step=1)
        
        updated_exit = f"Exit at {new_profit_target}% profit or {new_stop_loss}% loss"
        
        # Update plan button
        if st.button("💾 Update Today's Plan"):
            try:
                success = plan.update_daily_plan(
                    starting_balance=starting_balance,
                    market_condition=market_condition,
                    direction=direction,
                    contracts=contracts,
                    key_levels=updated_levels,
                    entry_condition=updated_entry,
                    exit_condition=updated_exit
                )
                if success:
                    st.success("Plan updated successfully!")
                    logger.info("Today's plan updated successfully")
                else:
                    st.error("Failed to update plan. Check inputs and try again.")
                    logger.error("Failed to update daily plan")
            except Exception as e:
                st.error(f"Error updating plan: {str(e)}")
                logger.error(f"Update plan error: {str(e)}")
        
        # Display updated plan
        st.divider()
        st.subheader("Current Plan")
        st.write(f"**Date:** {day_plan['Date']}")
        st.write(f"**Starting Balance:** ${starting_balance:.2f}")
        st.write(f"**Market Condition:** {market_condition}")
        st.write(f"**Direction:** {direction}")
        st.write(f"**Contracts:** {contracts}")
        st.write(f"**Key Levels:** {updated_levels}")
        st.write(f"**Entry Condition:** {updated_entry}")
        st.write(f"**Exit Condition:** {updated_exit}")

        if st.button("🔍 Show Current Market Analysis"):
            try:
                market = plan.get_market_analysis()
                if 'Error' in market:
                    st.error(f"Market analysis failed: {market['Error']}")
                    logger.error(f"Market analysis error: {market['Error']}")
                else:
                    st.subheader("📈 Current Market Analysis")
                    st.write(f"**IWM Price:** ${market['Current Price']:.2f}")
                    st.write(f"**Market Condition:** {market['Market Condition']}")
                    st.write(f"**Recommendation:** {market['Recommendation']}")
                    for k, v in market['Key Levels'].items():
                        st.write(f"**{k}:** {v:.2f}")
                    logger.info("Market analysis displayed")
            except Exception as e:
                st.error(f"Error retrieving market analysis: {str(e)}")
                logger.error(f"Market analysis error: {str(e)}")

    except Exception as e:
        st.error(f"Error loading today's plan: {str(e)}")
        logger.error(f"Today's plan error: {str(e)}")

elif page == "🧮 Record a Trade":
    st.header("🧮 Record Trade")

    try:
        trade_day = st.number_input("Enter Day # (1 - 100)", min_value=1, max_value=100, step=1)
        entry_price = st.number_input("Entry Price", min_value=0.0, step=0.01, format="%.2f")
        exit_price = st.number_input("Exit Price", min_value=0.0, step=0.01, format="%.2f")

        if st.button("💾 Record Trade"):
            try:
                success = plan.record_trade(trade_day, entry_price, exit_price)
                if success:
                    st.success(f"Trade recorded for Day {trade_day}!")
                    logger.info(f"Trade recorded for Day {trade_day}")
                else:
                    st.error("Failed to record trade. Check inputs and try again.")
                    logger.error("Failed to record trade")
            except Exception as e:
                st.error(f"Error recording trade: {str(e)}")
                logger.error(f"Trade recording error: {str(e)}")
    except Exception as e:
        st.error(f"Error in trade recording interface: {str(e)}")
        logger.error(f"Trade interface error: {str(e)}")

elif page == "📊 Performance Summary":
    st.header("📊 Performance Summary")

    try:
        if not plan.trade_journal:
            st.warning("No trades recorded yet.")
            logger.warning("No trades available for summary")
        else:
            trades = pd.DataFrame(plan.trade_journal)
            
            start_balance = trades.iloc[0]['Starting Balance']
            current_balance = trades.iloc[-1]['Ending Balance']
            total_gain = current_balance - start_balance
            growth_percent = (total_gain / start_balance) * 100
            
            wins = sum(trades['Gain/Loss'] > 0)
            losses = sum(trades['Gain/Loss'] < 0)
            win_rate = (wins / len(trades)) * 100
            
            st.subheader("Performance Metrics")
            st.write(f"**Starting Balance:** ${start_balance:.2f}")
            st.write(f"**Current Balance:** ${current_balance:.2f}")
            st.write(f"**Total Gain/Loss:** ${total_gain:.2f} ({growth_percent:.2f}%)")
            st.write(f"**Trades Completed:** {len(trades)}")
            st.write(f"**Win Rate:** {win_rate:.2f}% ({wins} wins, {losses} losses)")
            
            st.subheader("Recent Trades")
            st.dataframe(trades.tail(5)[['Date', 'Day', 'Direction', 'Contracts', 
                                        'Entry Price', 'Exit Price', 'Gain/Loss', 'Ending Balance']])
            
            st.subheader("💰 Balance Curve")
            fig, ax = plt.subplots()
            ax.plot(trades["Day"], trades["Ending Balance"], marker='o')
            ax.set_xlabel("Day")
            ax.set_ylabel("Account Balance ($)")
            ax.set_title("Account Growth Over Time")
            ax.grid(True)
            st.pyplot(fig)
            logger.info("Performance summary displayed")
    except Exception as e:
        st.error(f"Error generating performance summary: {str(e)}")
        logger.error(f"Performance summary error: {str(e)}")
