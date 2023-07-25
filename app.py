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

# Function to calculate the percentage of anomalies in the 'is_human' column
def calculate_anomaly_percentage(df):
    total_data_points = len(df)
    total_anomalies = df['is_human'].sum()
    percentage_anomalies = (total_anomalies / total_data_points) * 100
    return percentage_anomalies

# Streamlit app code
st.title('Sensor Data Visualization')
st.subheader('Temperature and Humidity')

# Add a refresh page button above the title
if st.button('Refresh Data'):
    df = fetch_data()
    st.success('Data has been refreshed.')

# Fetch the data
df = fetch_data()

# Calculate the average values
average_temperature = df['temperature'].mean()
average_humidity = df['humidity'].mean()
average_soil_humidity = df['soil_humid'].mean()

# Display the average values on top of the app
st.write('### Average Metrics')
st.write(f'Average Temperature: {average_temperature:.2f} °C')
st.write(f'Average Humidity: {average_humidity:.2f} %')
st.write(f'Average Soil Humidity: {average_soil_humidity:.2f}')

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

# Calculate percentage of anomalies
anomaly_percentage = calculate_anomaly_percentage(df)

# Display the percentage of anomalies using a 100% stacked bar chart
st.write('### Anomaly Detection')
fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(x=['Anomaly', 'Normal'], y=[anomaly_percentage, 100 - anomaly_percentage], palette=['red', 'green'])
plt.xlabel('Status', fontsize=12)
plt.ylabel('Percentage', fontsize=12)
plt.title('Percentage of Anomaly Detection', fontsize=14)
plt.ylim(0, 100)
plt.tight_layout()
st.pyplot(fig)
