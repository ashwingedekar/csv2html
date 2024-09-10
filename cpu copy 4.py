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
from sqlalchemy import create_engine
def remove_characters(text):
    cleaned_text = re.sub(r'\(�C\)|�C', '', text)
    return cleaned_text

#prtg_choice = input("Enter the PRTG you want (99.100, 101.100, 99.102): ")

#db_user = 'root'  # default MySQL user in XAMPP
#db_password = ''  # if you haven't set a password, leave it blank
#db_host = 'localhost'
#db_port = 3306  # MySQL default port
#db_name = 'prtg'

# Create a connection engine for XAMPP MySQL
#engine = create_engine(f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')



valid_choices = ["99.100", "101.100", "99.102"]

while True:
    prtg_choice = input("Enter a valid choice (99.100, 101.100, or 99.102): ")

    if prtg_choice in valid_choices:
        filename = f"server_address-{prtg_choice}.txt"
        with open(filename, "r") as file:
            server_parameters = dict(line.strip().split("=") for line in file)
        break
    else:
        print("Invalid input! Please enter either '99.100', '101.100', or '99.102'.")


server_address = server_parameters.get("server")
username = server_parameters.get("username")
passhash = server_parameters.get("passhash")
param = server_parameters.get("day")

current_datetime = datetime.now().strftime("%d_%B_%Y_%I_%M_%p")

if "99-102" in server_address:
    file_path = f"prtg-{current_datetime}-99.102.xml"
    output_file= f"prtg-{current_datetime}-99.102.txt"
       
elif "101-100" in server_address:
    file_path = f"prtg-{current_datetime}-101.100.xml"
    output_file= f"prtg-{current_datetime}-99.100.txt"
elif "99-100" in server_address:
    file_path = f"prtg-{current_datetime}-99.100.xml"
    output_file= f"prtg-{current_datetime}-99.100.txt"
else:
    file_path = f"prtg-{current_datetime}-default.xml"

#print(f"File path to save XML: {file_path}")

# first api call for all sensor tree

api_endpoint = f'https://{server_address}/api/table.xml?content=sensortree&username={username}&passhash={passhash}'

response = requests.get(api_endpoint)

# Check if the request was successful
if response.status_code == 200:
    print("Request successful!")
    print("Response content:")
    print(response.text)

    # Ensure the response content is not empty
    if response.text.strip():
        # Write the XML response to a file
        try:
            with open(file_path, "w") as file:
                file.write(response.text)
            print(f"XML data saved to {file_path}")
        except Exception as e:
            print(f"Error writing to file: {e}")
    else:
        print("The response text is empty. No data to save.")
else:
    print(f"Error: {response.status_code} - {response.text}")


encodings_to_try = ['utf-8', 'latin-1']

for encoding in encodings_to_try:
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            xml_content = file.read()
        break
    except UnicodeDecodeError:
        continue

cleaned_xml_content = remove_characters(xml_content)

try:
    root = ET.fromstring(cleaned_xml_content)
    tree = ET.ElementTree(root)

    # Save the modified XML back to a file
    tree.write(file_path)
    print("XML file cleaned successfully!")
except ET.ParseError as e:
    print("Error parsing XML:", e)


tree = ET.parse(file_path)
root = tree.getroot()

# Define sensor IDs
sensor_ids = []

for sensor in root.iter('sensor'):
    sensortype = sensor.find('sensortype')
    if sensortype is not None and sensortype.text == 'SNMP CPU Load':
        sensor_id = sensor.find('id')
        if sensor_id is not None:
            sensor_ids.append(sensor_id.text)

with open(output_file, 'w') as file:
    for i, sensor_id in enumerate(sensor_ids, start=1):
        file.write(f"id{i}={sensor_id}\n")


print("Sensor IDs for SNMP CPU Load sensors have been saved to:", output_file)

warnings.filterwarnings("ignore", category=DeprecationWarning)

flags = {}
id_prefix = 'id'
id_values = []

with open("min_max_flags.txt", "r") as file:
    for line in file:
        line = line.strip()
        if "=" in line:
            key, value = line.split("=")
            if key.startswith(id_prefix):
                id_values.append(value)
            else:
                flags[key] = value

with open(output_file, "r") as file:
    for line in file:
        line = line.strip()
        if "=" in line:
            key, value = line.split("=")
            if key.startswith(id_prefix):
                id_values.append(value)

print(id_values)

upper_warning_limits = {}

for id_value in tqdm(id_values, desc="Getting upper warning for Each ID"):
    try:
        api_endpoint_upper_warning = f'https://{server_address}/api/getobjectproperty.htm?subtype=channel&id={id_value}&subid=0&name=limitmaxwarning&show=nohtmlencode&username={username}&passhash={passhash}'
        response_upper_warning = requests.get(api_endpoint_upper_warning)
        
        if response_upper_warning.status_code != 200:
            print(f"Check parameters for: {id_value}")
            continue
            
        match_upper_warning = re.search(r'<result>(\d+)</result>', response_upper_warning.text)
        
        if match_upper_warning is not None:
            upper_warning_limits[id_value] = float(match_upper_warning.group(1))
            print(f"ID {id_value} ka upper warning limit hai: {upper_warning_limits[id_value]}")
        else:
            print(f"ID {id_value} ka upper warning limit nahi mila.")
            
    except Exception as e:
        print(f"Error getting upper warning limit for ID {id_value}: {e}")
        continue
print("Upper Warning Limits: ", upper_warning_limits)

output_data = []


complete_data = pd.DataFrame()

for id_value in tqdm(id_values, desc="Processing IDs"):
    parent_device_name = "N/A"
    sensor_device_name = "N/A"
    DeviceID = "N/A"
    
    try:
        # Fetch historic data CSV
        api_endpoint = f'https://{server_address}/api/historicdata.csv?id={id_value}&avg=0&sdate={flags.get("sdate")}&edate={flags.get("edate")}&username={username}&passhash={passhash}'
        response = requests.get(api_endpoint)
        df = pd.read_csv(io.StringIO(response.text))
        df['Sensor ID'] = id_value
        columns_to_drop = [f'Processor {i}(RAW)' for i in range(1, 129)]
        columns_to_drop.extend(['Date Time(RAW)', 'Total(RAW)', 'Coverage(RAW)'])
        df = df.drop(columns=columns_to_drop, errors='ignore')
        # Additional columns to drop
        
# Append karna data ko CSV file mein
        df.to_csv('complete_output.csv', mode='a', header=not complete_data.empty, index=False)

        # Append to complete data and save immediately to the CSV file
        
        complete_data = pd.concat([complete_data, df], ignore_index=True)  # Keep a copy in memory as well
 #       df.to_sql(name='sensor_data', con=engine, if_exists='append', index=False)

        
    except KeyError:
        print(f"CPU total column not found for ID: {id_value}")
        continue  
    
    
# Save the complete data to a CSV file
complete_data.to_csv('complete_output.csv', index=False)
