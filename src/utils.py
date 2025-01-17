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