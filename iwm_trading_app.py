

import streamlit as st
from IWMTradingPlan import IWMTradingPlan
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="IWM 0DTE Trading App", layout="centered")
st.title("📈 IWM 0DTE Trading Plan & Tracker")

# Initialize session state
if 'plan' not in st.session_state:
    st.session_state.plan = IWMTradingPlan()

plan = st.session_state.plan

# Sidebar navigation
page = st.sidebar.radio("Go to", ["📅 Today's Plan", "🧮 Record a Trade", "📊 Performance Summary"])

if page == "📅 Today's Plan":
    st.header("📅 Today's Trading Plan")
    day_plan = plan.get_daily_plan()
    st.write(f"**Date:** {day_plan['Date']}")
    st.write(f"**Starting Balance:** ${day_plan['Starting Balance']:.2f}")
    st.write(f"**Market Condition:** {day_plan['Market Condition']}")
    st.write(f"**Direction:** {day_plan['Direction']}")
    st.write(f"**Contracts:** {eval(day_plan['Contracts'])}")
    st.write(f"**Key Levels:** {day_plan['Key Levels']}")
    st.write(f"**Entry Condition:** {day_plan['Entry Condition']}")
    st.write(f"**Exit Condition:** {day_plan['Exit Condition']}")

    if st.button("🔍 Show Current Market Analysis"):
        market = plan.get_market_analysis()
        st.subheader("📈 Current Market Analysis")
        st.write(f"**IWM Price:** ${market['Current Price']:.2f}")
        st.write(f"**Market Condition:** {market['Market Condition']}")
        st.write(f"**Recommendation:** {market['Recommendation']}")
        for k, v in market['Key Levels'].items():
            st.write(f"**{k}:** {v:.2f}")

elif page == "🧮 Record a Trade":
    st.header("🧮 Record Trade")

    trade_day = st.number_input("Enter Day # (1 - 100)", min_value=1, max_value=100, step=1)
    entry_price = st.number_input("Entry Price", format="%.2f")
    exit_price = st.number_input("Exit Price", format="%.2f")

    if st.button("💾 Record Trade"):
        plan.record_trade(trade_day, entry_price, exit_price)

elif page == "📊 Performance Summary":
    st.header("📊 Performance Summary")

    if not plan.trade_journal:
        st.warning("No trades recorded yet.")
    else:
        st.session_state.plan.show_summary()

        # Plot balance curve
        st.subheader("💰 Balance Curve")
        trades = pd.DataFrame(plan.trade_journal)
        fig, ax = plt.subplots()
        ax.plot(trades["Day"], trades["Ending Balance"], marker='o')
        ax.set_xlabel("Day")
        ax.set_ylabel("Account Balance ($)")
        ax.set_title("Account Growth Over Time")
        ax.grid(True)
        st.pyplot(fig)

