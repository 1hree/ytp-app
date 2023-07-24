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
FROM "esp32_sensor"
WHERE
time >= now() - interval '60 minutes'
AND
("humidity" IS NOT NULL OR "temperature" IS NOT NULL)"""

# Define the query client
query_client = FlightSQLClient(
    host="us-east-1-1.aws.cloud2.influxdata.com",
    token=os.environ.get("INFLUXDB_TOKEN"),
    metadata={"bucket-name": "sensor_ytp"}
)

# Execute the query and convert to DataFrame
info = query_client.execute(query)
reader = query_client.do_get(info.endpoints[0].ticket)
data = reader.read_all()
df = data.to_pandas().sort_values(by="time")

# Convert timestamps to UTC+7 timezone
df['time'] = pd.to_datetime(df['time']).dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok')
df = df.drop("soil_moisture", axis=1)

# Streamlit app code
st.title('Sensor Data Visualization')
st.subheader('Temperature, Humidity, and Soil Humidity')

# Plot line charts for temperature, humidity, and soil humidity
fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(x='time', y='temperature', data=df, marker='o', markersize=5, color='blue', label='Temperature', ax=ax)
sns.lineplot(x='time', y='humidity', data=df, marker='o', markersize=5, color='green', label='Humidity', ax=ax)
sns.lineplot(x='time', y='soil_humid', data=df, marker='o', markersize=5, color='purple', label='Soil Humidity', ax=ax)
plt.xticks(rotation=45)
plt.xlabel('Time (UTC+7)', fontsize=12)
plt.ylabel('Values', fontsize=12)
plt.title('Temperature, Humidity, and Soil Humidity Variation over Time', fontsize=14)
plt.legend(fontsize=10)
plt.tight_layout()
st.pyplot(fig)

# Display the DataFrame
st.subheader('Sensor Data')
st.dataframe(df)
