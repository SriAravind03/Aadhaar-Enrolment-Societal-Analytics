from prophet import Prophet

def forecast_demand(df):

    ts = df.groupby('date')['total'].sum().reset_index()
    ts.columns = ['ds','y']

    model = Prophet(yearly_seasonality=True)
    model.fit(ts)

    future = model.make_future_dataframe(periods=60)
    forecast = model.predict(future)

    return forecast[['ds','yhat']]
