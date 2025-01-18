import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from .logger import logger

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