import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date, timedelta
import yfinance as yf
import plotly.graph_objects as go
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas_gbq


# API client
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
# client = bigquery.Client(credentials=credentials)

st.title('Stock Price Prediction')

stock = st.selectbox(
    'Select a stock:',
    ('AAPL (Apple)', 'TSLA (Tesla)', 'MSFT (Microsoft)', 'AMZN (Amazon)', 'GOOGL (Google)')
)
stock = stock.split(' ')[0]

today = date.today()
five_days_before = today - timedelta(days=5)
five_years_before = today - timedelta(days=1825)
start_date = st.date_input('Enter start date:', five_days_before, max_value=today-timedelta(days=1), min_value=five_years_before)
end_date = st.date_input('Enter end date:', today, max_value=today, min_value=five_years_before+timedelta(days=60))
five_days_after = end_date + timedelta(days=5)


# load stock price from yahoo
@st.cache(allow_output_mutation=True, ttl=600)
def get_stock(s, s_date, e_date):
    return yf.download(s, s_date, e_date)

df = get_stock(stock, start_date, end_date)
# df.index = df.index.date
if st.checkbox('Show stock price dataframe'):
    st.write(df)

# Load stock data from BigQuery/csv
# df = pd.read_csv('{}.csv'.format(stock))
# pred_df['Date'] = pred_pd.to_datetime(pred_df.Date, format='%Y-%m-%d').dt.date
# date_range = (df['Date'] > start_date) & (pred_df['Date'] <= end_date)
# df = df.loc[date_range]

#: load predicted price using stock vs all info from BQ
# @st.cache(allow_output_mutation=True, ttl=600)
def make_query(query):
    return pandas_gbq.read_gbq(query, credentials=credentials)

pred_df = make_query(
    "SELECT Date, predicted FROM `sublime-cargo-326805.stockPrediction.tw-pred` WHERE company = '{}' AND Date between '{}' AND '{}' ORDER BY Date;".format(stock, start_date, end_date)
)

# tw_pred_df = make_query(
#     "SELECT Date, predicted FROM `sublime-cargo-326805.stockPrediction.tweets_prediction` WHERE company = '{}' AND Date between '{}' AND '{}' ORDER BY Date;".format(stock, start_date, end_date)
# )

multi_pred_df = make_query(
    "SELECT Date, Close FROM `sublime-cargo-326805.stockPrediction.multi-forcast` WHERE Company = '{}' AND Date between '{}' AND '{}' ORDER BY Date;".format(stock, start_date, five_days_after)
)




# Graph
st.subheader('Plot')
fig, ax = plt.subplots()
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'], name='Actual')])

fig.add_trace(
    go.Scatter(
        x=pred_df['Date'],
        y=pred_df['predicted'],
        name='prediction made with tweets',
        line=dict(
            color='yellow'
        )
    )
)

fig.add_trace(
    go.Scatter(
        x=multi_pred_df['Date'],
        y=multi_pred_df['Close'],
        name='5 days predictions from LSTM',
        line=dict(
            color='cyan'
        )
    )
)

fig.update_layout(xaxis_rangeslider_visible=False,
                  title='Actual vs. Predicted {} stock price'.format(stock),
                  yaxis_title='$',
                  xaxis_title='Date')
st.plotly_chart(fig, use_container_width=True)
