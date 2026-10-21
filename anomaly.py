from sklearn.ensemble import IsolationForest

def detect_anomalies(df):

    features = df[['total']]

    model = IsolationForest(contamination=0.03, random_state=42)
    df['anomaly'] = model.fit_predict(features)

    return df[df['anomaly'] == -1]
