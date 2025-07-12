import streamlit as st
from IWMTradingPlan import IWMTradingPlan
import pandas as pd
import matplotlib.pyplot as plt
import re  # Import regex for string parsing

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
    
    # Use columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Date:** {day_plan['Date']}")
        
        # Editable starting balance
        starting_balance = st.number_input(
            "**Starting Balance ($)**", 
            value=float(day_plan['Starting Balance']),
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
        
        # Editable contracts - handle both int and string representations
        try:
            # Try to convert directly if it's an integer
            contract_value = int(day_plan['Contracts'])
        except:
            # If it's a string formula, evaluate it
            try:
                contract_value = eval(day_plan['Contracts'])
            except:
                contract_value = 1
                
        contracts = st.number_input(
            "**Contracts**", 
            value=contract_value, 
            min_value=1, 
            step=1
        )
    
    with col2:
        # Editable key levels - handle parsing errors
        st.write("**Key Levels**")
        try:
            levels_str = day_plan['Key Levels']
            # Extract numbers using regex
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", levels_str)
            if len(numbers) >= 3:
                pivot = float(numbers[0])
                r1 = float(numbers[1])
                s1 = float(numbers[2])
            else:
                # Default values if parsing fails
                pivot = 0.0
                r1 = 0.0
                s1 = 0.0
        except:
            pivot = 0.0
            r1 = 0.0
            s1 = 0.0
            
        pivot = st.number_input("Pivot", value=pivot, step=0.01, format="%.2f")
        r1 = st.number_input("R1", value=r1, step=0.01, format="%.2f")
        s1 = st.number_input("S1", value=s1, step=0.01, format="%.2f")
        
        # Save updated levels
        updated_levels = f"Pivot: {pivot:.2f}, R1: {r1:.2f}, S1: {s1:.2f}"
    
    # Editable entry condition - handle different formats
    entry_condition = day_plan['Entry Condition']
    threshold1 = 0.0
    threshold2 = 0.0
    
    try:
        # Try to extract numbers using regex
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", entry_condition)
        if len(numbers) >= 2:
            threshold1 = float(numbers[0])
            threshold2 = float(numbers[1])
    except:
        pass
    
    st.write("**Entry Condition**")
    col3, col4 = st.columns(2)
    with col3:
        new_threshold1 = st.number_input("Threshold 1", value=threshold1, step=0.01, format="%.2f")
    with col4:
        new_threshold2 = st.number_input("Threshold 2", value=threshold2, step=0.01, format="%.2f")
    
    if direction == "CALL":
        updated_entry = f"Enter CALL if pre-market high > {new_threshold1:.2f} or opening range high > {new_threshold2:.2f}"
    else:
        updated_entry = f"Enter PUT if pre-market low < {new_threshold1:.2f} or opening range low < {new_threshold2:.2f}"
    
    # Editable exit condition - handle different formats
    exit_condition = day_plan['Exit Condition']
    profit_target = 25
    stop_loss = 20
    
    try:
        # Try to extract numbers using regex
        numbers = re.findall(r"\d+", exit_condition)
        if len(numbers) >= 2:
            profit_target = int(numbers[0])
            stop_loss = int(numbers[1])
    except:
        pass
    
    st.write("**Exit Condition**")
    col5, col6 = st.columns(2)
    with col5:
        new_profit_target = st.number_input("Profit Target (%)", value=profit_target, min_value=1, max_value=100, step=1)
    with col6:
        new_stop_loss = st.number_input("Stop Loss (%)", value=stop_loss, min_value=1, max_value=100, step=1)
    
    updated_exit = f"Exit at {new_profit_target}% profit or {new_stop_loss}% loss"
    
    # Update plan button
    if st.button("💾 Update Today's Plan"):
        plan.update_daily_plan(
            starting_balance=starting_balance,
            market_condition=market_condition,
            direction=direction,
            contracts=contracts,
            key_levels=updated_levels,
            entry_condition=updated_entry,
            exit_condition=updated_exit
        )
        st.success("Plan updated successfully!")
    
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
