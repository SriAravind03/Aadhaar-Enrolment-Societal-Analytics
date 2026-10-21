import pandas as pd
import os

def load_and_clean(path):

    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    # Date parsing (Indian format)
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    df.dropna(subset=['date'], inplace=True)

    # Total transactions
    df['total'] = df[['age_0_5','age_5_17','age_18_greater']].sum(axis=1)

    # Time features
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year

    return df
