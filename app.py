import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from flightsql import FlightSQLClient

# Set InfluxDB token
os.environ['INFLUXDB_TOKEN'] = 'mYeX6-jJvpS0Laxo9Ws-fwBuGiq2dMA-97QTCWOJNl6URXCLdlrmPIqHTWnnq8E4NDMnNWy4JO7bsbXoAnjrTQ=='

# Define the query
query = """SELECT *
FROM "esp32_sensor_full"
"""


# Define the query client
query_client = FlightSQLClient(
    host="us-east-1-1.aws.cloud2.influxdata.com",
    token=os.environ.get("INFLUXDB_TOKEN"),
    metadata={"bucket-name": "sensor_ytp"}
)

# Function to fetch data and process it
def fetch_data():
    info = query_client.execute(query)
    reader = query_client.do_get(info.endpoints[0].ticket)
    data = reader.read_all()
    df = data.to_pandas().sort_values(by="time")

    # Convert timestamps to UTC+7 timezone
    df['time'] = pd.to_datetime(df['time']).dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok')
    return df

# Streamlit app code
st.title('Sensor Data Visualization')

# Fetch the data
df = fetch_data()

# Calculate the average values
average_temperature = df['temperature'].mean()
average_humidity = df['humidity'].mean()
average_soil_humidity = df['soil_humid'].mean()

# Display the average values on top of the app
col1, col2, col3 = st.columns(3)
col1.metric("Temperature", f"{average_temperature:.2f} °C", "1.2 °C")
col2.metric("Humidity", f"{average_humidity:.2f} %", "4%")
col3.metric("Soil Humidity", f"{average_soil_humidity:.2f}", "0.1")

# Add a refresh page button below the metrics
if st.button('Refresh Data'):
    df = fetch_data()
    st.success('Data has been refreshed.')

# Plot line chart for temperature and humidity
plt.figure(figsize=(10, 6))
sns.lineplot(x='time', y='temperature', data=df, marker='o', markersize=5, color='blue', label='Temperature')
sns.lineplot(x='time', y='humidity', data=df, marker='o', markersize=5, color='green', label='Humidity')
plt.xticks(rotation=45)
plt.xlabel('Time (UTC+7)', fontsize=12)
plt.ylabel('Values', fontsize=12)
plt.title('Temperature and Humidity Variation over Time', fontsize=14)
plt.legend(fontsize=10)
plt.tight_layout()
st.pyplot()

# Streamlit app code for Soil Humidity plot
st.subheader('Soil Humidity')

# Plot line chart for soil humidity
plt.figure(figsize=(10, 6))
sns.lineplot(x='time', y='soil_humid', data=df, marker='o', markersize=5, color='purple', label='Soil Humidity')
plt.xticks(rotation=45)
plt.xlabel('Time (UTC+7)', fontsize=12)
plt.ylabel('Soil Humidity', fontsize=12)
plt.title('Soil Humidity Variation over Time', fontsize=14)
plt.legend(fontsize=10)
plt.tight_layout()
st.pyplot()

# Streamlit app code for "is_human" plot
st.subheader('Is Human')

# Reformat the x-axis labels to display only date and time (DD HH:MM)
df['time_formatted'] = df['time'].dt.strftime('%d %H:%M')

# Plot bar chart for "is_human" column with formatted x-axis labels
plt.figure(figsize=(10, 6))
sns.barplot(x='time_formatted', y='is_human', data=df, color='orange', label='Is Human')
plt.xticks(rotation=45)
plt.xlabel('Time (UTC+7)', fontsize=12)
plt.ylabel('Is Human', fontsize=12)
plt.title('Is Human Detection over Time', fontsize=14)
plt.legend(fontsize=10)
plt.tight_layout()
st.pyplot()
