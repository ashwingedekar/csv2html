import requests
import xml.etree.ElementTree as ET
import re
import csv
import os
import pandas as pd
from io import StringIO
import warnings
from datetime import datetime
from tqdm import tqdm
import io
import webbrowser


import pandas as pd

# Read the CSV file
df = pd.read_csv('my.csv')

# Initialize HTML content
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sensor Data</title>
    <style>
        .hidden { display: none; }
    </style>
    <script>
        function toggleDetails(id) {
            var element = document.getElementById(id);
            if (element.classList.contains('hidden')) {
                element.classList.remove('hidden');
            } else {
                element.classList.add('hidden');
            }
        }
    </script>
</head>
<body>
<ul>
"""

# Group by 'Message' and count occurrences
message_group = df.groupby('Message').size()

for message, count in message_group.items():
    html_content += f"<li><a onclick=\"toggleDetails('{message.replace(' ', '_')}')\">{message} ({count})</a>"
    html_content += f"<ul id='{message.replace(' ', '_')}' class='hidden'>"
    
    # Filter dataframe for the current message
    filtered_df = df[df['Message'] == message]
    
    # Group by 'Device Name'
    device_group = filtered_df.groupby('Device Name')
    
    for device_name, device_data in device_group:
        html_content += f"<li><a onclick=\"toggleDetails('{message.replace(' ', '_')}_{device_name.replace(' ', '_')}')\">Device Name : {device_name}</a>"
        html_content += f"<ul id='{message.replace(' ', '_')}_{device_name.replace(' ', '_')}' class='hidden'>"
        
        # Group by 'Sensor Name' and 'Sensor ID'
        sensor_group = device_data.groupby(['Sensor Name', 'Sensor ID'])
        
        for (sensor_name, sensor_id), sensor_data in sensor_group:
            html_content += f"<li><a onclick=\"toggleDetails('{message.replace(' ', '_')}_{device_name.replace(' ', '_')}_{sensor_name.replace(' ', '_')}_{sensor_id}')\"><b>Sensor Name :</b>{sensor_name} <b>Sensor ID:</b> {sensor_id}</a>"
            html_content += f"<ul id='{message.replace(' ', '_')}_{device_name.replace(' ', '_')}_{sensor_name.replace(' ', '_')}_{sensor_id}' class='hidden'>"
            
            # Add details
            for _, row in sensor_data.iterrows():
                html_content += f"<li>Date: {row['Date']} - Total CPU: {row['Total CPU']}</li>"
                
            html_content += "</ul></li>"
        
        html_content += "</ul></li>"
    
    html_content += "</ul></li>"

html_content += """
</ul>
</body>
</html>
"""

# Write HTML content to file
with open('output.html', 'w') as file:
    file.write(html_content)
