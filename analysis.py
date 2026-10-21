import pandas as pd
from sklearn.cluster import KMeans

def time_trends(df):
    return df.groupby('date')['total'].sum().reset_index()

def district_pressure(df):
    agg = df.groupby('district')['total'].mean().reset_index()
    return agg.sort_values('total', ascending=False)

def migration_clusters(df):
    agg = df.groupby('pincode')['total'].mean().reset_index()

    kmeans = KMeans(n_clusters=3, random_state=42)
    agg['cluster'] = kmeans.fit_predict(agg[['total']])

    return agg
