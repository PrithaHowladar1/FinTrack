import pandas as pd

def clean_dataframe(df):
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    df['date'] = pd.to_datetime(df['date'])
    for col in ['debit', 'credit', 'amount', 'month_number']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df