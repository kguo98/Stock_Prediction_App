import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date, timedelta
import yfinance as yf
import plotly.graph_objects as go
from google.oauth2 import service_account
from google.cloud import bigquery


# API client
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

st.title('Stock Price Prediction')

# stock = st.text_input('Enter stock ticker:', placeholder='AAPL')
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
# predict for x days future INSTEAD OF a single day???

# load stock price from yahoo
@st.cache(allow_output_mutation=True, ttl=600)
def get_stock(s, s_date, e_date):
    return yf.download(s, s_date, e_date)

df = get_stock(stock, start_date, end_date)
df.index = df.index.date
if st.checkbox('Show stock price dataframe'):
    st.write(df)

# Load stock data from BigQuery/csv
# df = pd.read_csv('{}.csv'.format(stock))
# pred_df['Date'] = pred_pd.to_datetime(pred_df.Date, format='%Y-%m-%d').dt.date
# date_range = (df['Date'] > start_date) & (pred_df['Date'] <= end_date)
# df = df.loc[date_range]

#TODO: load predicted data
@st.cache(allow_output_mutation=True, ttl=600)
def query_predicted(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    rows = [dict(row) for row in rows_raw]
    return rows

pred_df = query_predicted(
    "SELECT Date, Predictions FROM `sublime-cargo-326805.stockPrediction.prediction` WHERE Date between '{}' AND '{}' ORDER BY Date;".format(start_date, end_date)
)
pred_df
# pred_df = pd.read_csv('predictions.csv')[['Date', 'Predictions']]
# pred_df['Date'] = pd.to_datetime(pred_df.Date, format='%Y-%m-%d').dt.date
# date_range = (pred_df['Date'] >= start_date) & (pred_df['Date'] < end_date)
# pred_df = pred_df.loc[date_range]


#TODO: load tweets/news data

# st.subheader('Data Overview')
# st.write(df.describe())

# st.subheader('Plot')
fig, ax = plt.subplots()
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'], name='Actual')])

fig.add_trace(
    go.Scatter(
        x=pred_df['Date'],
        y=pred_df['Predictions'],
        name='Predicted',
        line=dict(
            color='yellow'
        )
    )
)
# ax.plot(df['High'], label='High')
# ax.plot(df['Low'], label='Low')
# ax.plot(df['Close'], label='Actual Close')
# ax.set_xlabel('Date')
# ax.set_ylabel('$')
# ax.legend()
# st.pyplot(fig)
fig.update_layout(xaxis_rangeslider_visible=False,
                  title='Actual vs. Predicted {} stock price'.format(stock),
                  yaxis_title='$',
                  xaxis_title='Date')
st.plotly_chart(fig, use_container_width=True)