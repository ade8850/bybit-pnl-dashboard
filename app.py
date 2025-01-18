import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.bybit_client import BybitClient
from src.db_manager import DBManager
from src.config import SUPPORTED_TIMEFRAMES, DEFAULT_TIMEFRAME
from src.logger import logger, clear_logs
from src.utils import style_pnl_column, style_side_column
from src.plotting import plot_detailed_pnl_chart, plot_aggregated_pnl_chart

st.set_page_config(page_title="Bybit PNL Dashboard", layout="wide")

def get_initial_data(db, client):
    """Carica i dati iniziali nel database se è vuoto"""
    try:
        df = db.get_trades()
        if df.empty:
            logger.info("No data in database, loading initial data from Bybit...")
            with st.spinner("Loading initial data from Bybit..."):
                # Carichiamo prima l'ultima settimana
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)
                df = client.get_pnl_dataframe(start_time, end_time)
                if not df.empty:
                    db.save_trades(df)
                    st.success("Initial data loaded successfully!")
                else:
                    st.error("No data available from Bybit")
        return not df.empty
    except Exception as e:
        logger.error(f"Error loading initial data: {str(e)}")
        st.error(f"Error loading data: {str(e)}")
        return False

def main():
    # Clear logs at every page refresh
    clear_logs()
    
    # Inizializza il DBManager nello state di Streamlit
    if 'db' not in st.session_state:
        st.session_state.db = DBManager()
    
    # Inizializza o incrementa il contatore di refresh nello state
    if 'refresh_counter' not in st.session_state:
        st.session_state.refresh_counter = 0
        
    # Layout header con titolo e pulsanti refresh
    col_title, col_refresh_week, col_refresh_year = st.columns([6, 1, 1])
    
    with col_title:
        st.title("Bybit PNL Dashboard")
        
    with col_refresh_week:
        if st.button("🔄 Refresh Week", use_container_width=True, help="Refresh last week's data"):
            st.session_state.refresh_counter += 1
            client = BybitClient()
            with st.spinner("Loading last week's data..."):
                # Carica solo l'ultima settimana
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)
                new_df = client.get_pnl_dataframe(start_time, end_time)
                
                if not new_df.empty:
                    # Carica i dati esistenti
                    existing_df = st.session_state.db.get_trades()
                    
                    if not existing_df.empty:
                        # Rimuovi i dati dell'ultima settimana dal DataFrame esistente
                        mask = existing_df['updatedTime'] < start_time
                        existing_df = existing_df[mask]
                        
                        # Concatena i nuovi dati con quelli esistenti
                        combined_df = pd.concat([existing_df, new_df])
                        st.session_state.db.save_trades(combined_df)
                    else:
                        # Se non ci sono dati esistenti, salva solo i nuovi
                        st.session_state.db.save_trades(new_df)
                        
                    st.success("Weekly data refreshed successfully!")
                else:
                    st.error("No new data available from Bybit")
                    return
                
    with col_refresh_year:
        if st.button("📅 Load Year", use_container_width=True, help="Load full year of data"):
            st.session_state.refresh_counter += 1
            client = BybitClient()
            with st.spinner("Loading full year of data..."):
                end_time = datetime.now()
                start_time = end_time - timedelta(days=365)
                df = client.get_pnl_dataframe(start_time, end_time)
                if not df.empty:
                    st.session_state.db.save_trades(df)
                    st.success("Full year data loaded successfully!")
                else:
                    st.error("No data available from Bybit")
                    return
            
    logger.info(f"Starting application (refresh #{st.session_state.refresh_counter})")
    
    # Carica i dati iniziali se necessario
    client = BybitClient()
    if not get_initial_data(st.session_state.db, client):
        return
        
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Period selection
    period = st.sidebar.selectbox(
        "Period",
        ["7D", "1M", "3M", "6M", "1Y", "YTD", "All"],
        index=1
    )
    
    # Calculate start and end dates
    end_time = datetime.now()
    if period == "7D":
        start_time = end_time - timedelta(days=7)
    elif period == "1M":
        start_time = end_time - timedelta(days=30)
    elif period == "3M":
        start_time = end_time - timedelta(days=90)
    elif period == "6M":
        start_time = end_time - timedelta(days=180)
    elif period == "1Y":
        start_time = end_time - timedelta(days=365)
    elif period == "YTD":
        start_time = datetime(end_time.year, 1, 1)
    else:  # All
        start_time = None
        
    logger.info(f"Selected period: {period} ({start_time} to {end_time})")
    
    # Timeframe selection
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        SUPPORTED_TIMEFRAMES,
        index=SUPPORTED_TIMEFRAMES.index(DEFAULT_TIMEFRAME)
    )
    
    # Chart type selection
    chart_type = st.sidebar.selectbox(
        "Chart Type",
        ["Aggregated", "Detailed"],
        index=0
    )
    
    # Load filtered data from database
    df = st.session_state.db.get_trades(start_time, end_time)
    
    if df.empty:
        st.error("No data available for the selected period")
        logger.warning("No data available for the selected period")
        return
            
    # Sort DataFrame with most recent first
    df = df.sort_values('updatedTime', ascending=False)
            
    # General statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_pnl = df['closedPnl'].sum()
    total_trades = len(df)
    win_rate = (df['closedPnl'] > 0).mean() * 100
    avg_pnl = df['closedPnl'].mean()
    
    col1.metric("Total PNL", f"{total_pnl:.2f}")
    col2.metric("Total Trades", total_trades)
    col3.metric("Win Rate", f"{win_rate:.1f}%")
    col4.metric("Avg PNL", f"{avg_pnl:.2f}")
    
    # For plotting, sort chronologically
    df_plot = df.sort_values('updatedTime').set_index('updatedTime')
    logger.debug(f"Plotting DataFrame shape: {df_plot.shape}")
    
    # PNL chart
    try:
        if chart_type == "Detailed":
            fig = plot_detailed_pnl_chart(df_plot, "PNL Analysis")
        else:
            fig = plot_aggregated_pnl_chart(df_plot, timeframe, f"PNL Analysis ({timeframe})")
            
        st.plotly_chart(fig, use_container_width=True)
        logger.info("Chart created and displayed successfully")
        
    except Exception as e:
        logger.error("Error creating chart", exc_info=True)
        st.error(f"Error creating chart: {str(e)}")
    
    # Aggregated data
    st.header("Aggregated Data")
    aggregated_df = client.aggregate_pnl(df, timeframe)
    # Sort aggregated data with most recent first and apply styling
    aggregated_df = aggregated_df.sort_values('updatedTime', ascending=False)
    
    # Format duration in minutes to "Xh Ym"
    def format_duration(mins):
        if pd.isna(mins):
            return "0m"
        hours = int(mins // 60)
        minutes = int(mins % 60)
        return f"{hours}h {minutes}m"
    
    # Convert durations to human readable format
    if 'duration_total' in aggregated_df.columns:
        aggregated_df['duration'] = aggregated_df['duration_total'].apply(format_duration)
    if 'duration_avg' in aggregated_df.columns:
        aggregated_df['avg_duration'] = aggregated_df['duration_avg'].apply(format_duration)
    
    # Riordina le colonne
    columns_order = ['updatedTime', 'trades', 'fillCount', 'closedPnl', 'pct', 'winRate', 'avg_duration', 'duration']
    aggregated_df = aggregated_df[columns_order]
    
    st.dataframe(
        aggregated_df.style.applymap(
            style_pnl_column,
            subset=['closedPnl', 'pct']
        ).format({
            'closedPnl': '{:.2f}',
            'pct': '{:.2f}%',
            'winRate': '{:.1f}%'
        })
    )
    
    # Trade details
    st.header("Trade Details")
    # Calcola la durata in ore e minuti
    df['duration'] = (pd.to_datetime(df['updatedTime']) - pd.to_datetime(df['createdTime'])).apply(
        lambda x: f"{int(x.total_seconds()//3600)}h {int((x.total_seconds()%3600)/60)}m"
    )
    trades_df = df[[
        'symbol', 'side', 'closedSize', 'avgEntryPrice', 'avgExitPrice',
        'closedPnl', 'pct', 'duration', 'createdTime', 'updatedTime'
    ]]
    st.dataframe(
        trades_df.style.applymap(
            style_pnl_column,
            subset=['closedPnl', 'pct']
        ).applymap(
            style_side_column,
            subset=['side']
        ).format({
            'pct': '{:.2f}%',
            'closedPnl': '{:.2f}',
            'avgEntryPrice': '{:.2f}',
            'avgExitPrice': '{:.2f}'
        })
    )

if __name__ == "__main__":
    main()