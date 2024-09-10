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
df = pd.read_csv('abcd.csv')

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

# Group by 'country' and count occurrences
country_group = df.groupby('Country').size()

for country, count in country_group.items():
    html_content += f"<li><a onclick=\"toggleDetails('{country.replace(' ', '_')}')\">{country} ({count})</a>"
    html_content += f"<ul id='{country.replace(' ', '_')}' class='hidden'>"
    
    # Filter dataframe for the current country
    filtered_df = df[df['Country'] == country]
    
    # Group by 'company Name'
    company_name = filtered_df.groupby('Company')
    
    for company, device_data in company_name:
        html_content += f"<li><a onclick=\"toggleDetails('{country.replace(' ', '_')}_{company.replace(' ', '_')}')\">Device Name : {company}</a>"
        html_content += f"<ul id='{country.replace(' ', '_')}_{company.replace(' ', '_')}' class='hidden'>"
        
        # Group by 'Sensor Name' and 'Sensor ID'
        full_name_group = device_data.groupby(['First Name', 'Last Name'])
        
        for (sensor_name, sensor_id), sensor_data in full_name_group:
            html_content += f"<li><a onclick=\"toggleDetails('{country.replace(' ', '_')}_{company.replace(' ', '_')}_{sensor_name.replace(' ', '_')}_{sensor_id}')\"><b>Sensor Name :</b>{sensor_name} <b>Sensor ID:</b> {sensor_id}</a>"
            html_content += f"<ul id='{country.replace(' ', '_')}_{company.replace(' ', '_')}_{sensor_name.replace(' ', '_')}_{sensor_id}' class='hidden'>"
            
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
