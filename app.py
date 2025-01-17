import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.bybit_client import BybitClient
from src.config import SUPPORTED_TIMEFRAMES, DEFAULT_TIMEFRAME
from plotly.subplots import make_subplots
from src.logger import logger

st.set_page_config(page_title="Bybit PNL Dashboard", layout="wide")

def plot_detailed_pnl_chart(df, title):
    """Creates a detailed performance chart with both cumulative and daily PNL"""
    logger.info(f"Creating detailed chart with {len(df)} trades")
    logger.debug(f"PNL range: Min={df['closedPnl'].min():.2f}, Max={df['closedPnl'].max():.2f}")
    
    try:
        # Aumentiamo lo spacing tra i subplot
        fig = make_subplots(rows=2, cols=1, 
                          row_heights=[0.6, 0.4], 
                          vertical_spacing=0.1)
        logger.debug("Created subplots")
        
        cum_pnl = df['closedPnl'].cumsum()
        trade_pnl = df['closedPnl']
        logger.debug("Calculated PNL series")
        
        # Colori più brillanti per le barre
        bar_colors = ['rgba(0, 255, 0, 1)' if x >= 0 else 'rgba(255, 0, 0, 1)' for x in trade_pnl]
        
        # Aggiungiamo le barre con colori più brillanti e bordo
        logger.debug("Adding trade bars...")
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=trade_pnl,
                name='Trade PNL',
                marker=dict(
                    color=bar_colors,
                    line=dict(
                        color=['darkgreen' if x >= 0 else 'darkred' for x in trade_pnl],
                        width=1
                    )
                ),
                opacity=1,
                width=300000  # ~3.5 giorni in millisecondi
            ),
            row=2, col=1
        )
        logger.debug("Added trade bars successfully")
        
        # Aggiungiamo la linea del PNL cumulativo
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=cum_pnl,
                mode='lines',
                name='Cumulative PNL',
                line=dict(
                    color='green' if cum_pnl.iloc[-1] >= 0 else 'red',
                    width=2
                )
            ),
            row=1, col=1
        )
        
        # Zero lines
        fig.add_hline(y=0, line_width=2, line_dash="solid", 
                     line_color="rgba(255, 255, 255, 0.5)",
                     row=1, col=1)
        fig.add_hline(y=0, line_width=2, line_dash="solid", 
                     line_color="rgba(255, 255, 255, 0.5)",
                     row=2, col=1)
        
        fig.update_layout(
            title=title,
            showlegend=True,
            hovermode='x unified',
            height=800,
            template="plotly_dark",
            bargap=0.1  # Spazio tra le barre
        )
        
        # Update axes con range espliciti
        max_pnl = max(abs(trade_pnl.min()), abs(trade_pnl.max()))
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Cumulative PNL", row=1, col=1)
        fig.update_yaxes(
            title_text="Trade PNL",
            range=[-max_pnl*1.1, max_pnl*1.1],  # Range esplicito con padding
            row=2, col=1
        )
        logger.debug("Updated layout successfully")
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating detailed chart: {str(e)}", exc_info=True)
        raise

def plot_aggregated_pnl_chart(df, timeframe, title):
    """Creates a chart with aggregated PNL based on the selected timeframe"""
    logger.info(f"Creating aggregated chart for timeframe {timeframe}")
    
    try:
        fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], vertical_spacing=0.03)
        
        # Resample data based on timeframe
        resampled = df.resample(
            {'1d': 'D', '1w': 'W', '1M': 'M'}[timeframe]
        ).agg({'closedPnl': 'sum'})
        
        logger.debug(f"Resampled data shape: {resampled.shape}")
        
        cum_pnl = resampled['closedPnl'].cumsum()
        period_pnl = resampled['closedPnl']
        
        # Colori più brillanti anche per il grafico aggregato
        bar_colors = ['rgba(0, 255, 0, 1)' if x >= 0 else 'rgba(255, 0, 0, 1)' for x in period_pnl]
        
        # Period PNL bars
        fig.add_trace(
            go.Bar(
                x=resampled.index,
                y=period_pnl,
                name=f'{timeframe} PNL',
                marker=dict(
                    color=bar_colors,
                    line=dict(
                        color=['darkgreen' if x >= 0 else 'darkred' for x in period_pnl],
                        width=1
                    )
                ),
                opacity=1
            ),
            row=2, col=1
        )
        
        # Cumulative PNL line
        fig.add_trace(
            go.Scatter(
                x=resampled.index,
                y=cum_pnl,
                mode='lines',
                name='Cumulative PNL',
                line=dict(color='green' if cum_pnl.iloc[-1] >= 0 else 'red', width=2)
            ),
            row=1, col=1
        )
        
        # Zero lines
        fig.add_hline(y=0, line_width=2, line_dash="solid", 
                     line_color="rgba(255, 255, 255, 0.5)",
                     row=1, col=1)
        fig.add_hline(y=0, line_width=2, line_dash="solid", 
                     line_color="rgba(255, 255, 255, 0.5)",
                     row=2, col=1)
        
        fig.update_layout(
            title=title,
            showlegend=True,
            hovermode='x unified',
            height=800,
            template="plotly_dark"
        )
        
        # Update axes
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Cumulative PNL", row=1, col=1)
        fig.update_yaxes(title_text=f"{timeframe} PNL", row=2, col=1)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating aggregated chart: {str(e)}", exc_info=True)
        raise

def style_pnl_column(val):
    """Helper function to style PNL values and percentages with colors"""
    if val > 0:
        color = 'rgb(0, 255, 0)'  # Verde brillante come nell'istogramma
    elif val < 0:
        color = 'rgb(255, 0, 0)'  # Rosso
    else:
        color = 'gray'
    return f'color: {color}'

def style_side_column(val):
    """Helper function to style side values (Buy/Sell)"""
    if val == 'Buy':
        color = 'rgb(0, 255, 0)'  # Verde brillante
    else:  # Sell
        color = 'rgb(255, 0, 0)'  # Rosso
    return f'color: {color}'

def main():
    # Inizializza o incrementa il contatore di refresh nello state
    if 'refresh_counter' not in st.session_state:
        st.session_state.refresh_counter = 0
        
    # Layout header con titolo e pulsante refresh
    col_title, col_refresh = st.columns([6, 1])
    with col_title:
        st.title("Bybit PNL Dashboard")
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.refresh_counter += 1
            
    logger.info(f"Starting application (refresh #{st.session_state.refresh_counter})")
    
    # Initialize client
    client = BybitClient()
    
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
    
    # Chart type selection con Aggregated come default
    chart_type = st.sidebar.selectbox(
        "Chart Type",
        ["Aggregated", "Detailed"],  # Aggregated è il primo nell'elenco
        index=0  # Seleziona il primo elemento (Aggregated)
    )
    
    # Load data
    with st.spinner("Loading data..."):
        logger.info("Loading data from Bybit...")
        df = client.get_pnl_dataframe(start_time, end_time)
        
        if df.empty:
            st.error("No data available for the selected period")
            logger.warning("No data available for the selected period")
            return
            
        logger.info(f"Loaded {len(df)} trades")
        
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
        trades_df = df[[
            'symbol', 'side', 'closedSize', 'avgEntryPrice', 'avgExitPrice',
            'closedPnl', 'pct', 'createdTime', 'updatedTime'
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