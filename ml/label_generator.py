def generate_labels(trade_df):
    labels = []
    for idx, row in trade_df.iterrows():
        if row['exit_reason'] == 'TRAILING_STOP':
            labels.append('TRAILING_STOP')
        elif row['exit_reason'] == 'TIMEOUT':
            labels.append('TIMEOUT')
        elif row['pnl_pct'] <= -0.5:
            labels.append('SL')
        elif row['pnl_pct'] >= 2.0:
            labels.append('TP3')
        elif row['pnl_pct'] >= 1.0:
            labels.append('TP2-Partial')
        elif row['pnl_pct'] >= 0.5:
            labels.append('TP1-Partial')
        else:
            labels.append('Neutral')
    trade_df['exit_reason'] = labels
    return trade_df
