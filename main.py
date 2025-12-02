import asyncio
from bleak import BleakScanner, BleakClient
import struct
from typing import List
from dash import Dash, html, dcc, callback, Output, Input
import threading
import re 
import csv 
import os
import time

DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX" 
DEVICE_NAME = "ESP32H2_BLE"
DATA_CHARACTERISTIC_UUID = ["abcd1234-ab12-cd34-ef56-1234567890ab"] 
LISTENING_DURATION = 86400
CSV_FILE_PATH = "sensor_data.csv"
CSV_HEADERS = ['Time', 'Battery', 'LightLUX', 'UV_Index', 'Magnetic_X', 'Magnetic_Y', 'Magnetic_Z', 'CO2ppm', 'TempC', 'HumRH']

current_csv_file = None

class BLE_DEVICE():
    def __init__(self, address: str, name: str, characteristic_uuid: List[str], listening_duration: int):
        self.address = address
        self.name = name
        self.characteristic_uuid = characteristic_uuid
        self.listening_duration = listening_duration
        self.client: BleakClient = None
        self.init = False
        self.last_message = "NA"
        self.last_data = {}
        self.last_message_time = time.time()
        self.delta_time_notification = 0
        self.pause_acquisition = True

device = BLE_DEVICE(DEVICE_ADDRESS, DEVICE_NAME, DATA_CHARACTERISTIC_UUID, LISTENING_DURATION)

def parse_and_prepare_row(data_string: str) -> dict:
    data = {}
    
    sections = [s.strip() for s in data_string.split('|')]
    
    for section in sections:
        if section.startswith('Time:'):
            data['Time'] = time.strftime("%H:%M:%S", time.localtime())
            
        elif section.startswith('Battery:'):
            value = section.split(':')[1].strip().replace('%', '')
            data['Battery'] = float(value)
            
        elif 'Light(LUX)' in section:
            value = section.split(':')[1].strip()
            data['LightLUX'] = float(value)
            
        elif 'UV_Index' in section:
            value = section.split(':')[1].strip()
            data['UV_Index'] = float(value)
            
        elif 'Magnetic Field' in section:
            m = re.search(r'X:([-\d.]+),\s*Y:([-\d.]+),\s*Z:([-\d.]+)', section)
            if m:
                data['Magnetic_X'] = float(m.group(1))
                data['Magnetic_Y'] = float(m.group(2))
                data['Magnetic_Z'] = float(m.group(3))
                
        elif 'CO2(ppm)' in section:
            co2_match = re.search(r'CO2\(ppm\):([\d.]+)', section)
            if co2_match:
                data['CO2ppm'] = float(co2_match.group(1))

            temp_match = re.search(r'Temp\(C\):([-\d.]+)', section)
            if temp_match:
                data['TempC'] = float(temp_match.group(1))
            

            hum_match = re.search(r'Hum\(%RH\):([\d.]+)', section)
            if hum_match:
                data['HumRH'] = float(hum_match.group(1))
    
    final_row = {header: data.get(header, 'NA') for header in CSV_HEADERS}
    
    return final_row

def setup_csv():
    global current_csv_file
    csv_count = 0
    current_dir = os.getcwd()
    for file in os.listdir(current_dir):
        if file.endswith(".csv"):
            csv_count += 1
    current_csv_file = f"{csv_count}_{CSV_FILE_PATH}"
    with open(current_csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        print(f"CSV file created/recreated: {current_csv_file}")


def write_to_csv(data_row: dict):
    global current_csv_file
    with open(current_csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writerow(data_row)
        
def display_acquisition_status():
    global device
    status = "Paused" if device.pause_acquisition else "Running"
    return html.P(f"Data Acquisition status: {status}")

app = Dash(__name__)
app.layout = html.Div([
    html.H1("BLE Temperature Monitor"),
    dcc.Interval(id='interval', n_intervals=0),
    html.P(id="last-message", children=f"Last Message: {device.last_message}"),
    html.Button("Pause / Resume Acquisition", id="toggle-acquisition", n_clicks=0),
    html.P(id="data-acquisition-status", children=f"Data Acquisition status: Running"),
])

@app.callback(
    Output("last-message", "children"),
    Input("interval", "n_intervals")
)
def update_last_message(n):
    return f"Last Message: {device.last_message}"

@app.callback(
    Output("data-acquisition-status", "children"),
    Input("toggle-acquisition", "n_clicks")
)
def toggle_acquisition_status(n_clicks):
    global device
    if n_clicks % 2 == 1:
        device.pause_acquisition = False
    else:
        device.pause_acquisition = True
    return f"Data acquisition status: {'Paused' if device.pause_acquisition else 'Running'}"

async def scan_and_connect(device: BLE_DEVICE):
    print("Scanning...")
    
    target_address = device.address 
    
    while not device.init:
        devices = await BleakScanner.discover(timeout=5.0)

        for d in devices:
            print(f"Found device: {d.name} ({d.address})")

        found_device_info = next((d for d in devices if d.name == device.name), None) 
        
        if found_device_info:
            device.address = found_device_info.address
            target_address = device.address
            device.init = True
            print(f"Device found: {device.name} ({device.address})")
        else:
            print(f"Device not found.")
        await asyncio.sleep(5.0)
    
    while True:
        try:
            print(f"\nAttempting to connect to {target_address}...")
            
            async with BleakClient(target_address) as client:
                if client.is_connected:
                    print(f"Connected!")
                    await acquire_data(client, device) 
                else:
                    print("Connection failed.")
                    
        except Exception as e:
            print(f"Connection error: {e}")
            
        await asyncio.sleep(5.0)


async def acquire_data(client: BleakClient, device: BLE_DEVICE):
    active_uuids = []
    services = client.services

    for service in services:
        print(f"\n[SERVICE] UUID: {service.uuid} (Handle: {service.handle})")
        for char in service.characteristics:
            print(f"  [CHAR] UUID: {char.uuid}")
            print(f"    Properties: {char.properties}")
            if "notify" in char.properties and char.uuid not in device.characteristic_uuid:
                device.characteristic_uuid.append(char.uuid)

    try:
        for uuid in device.characteristic_uuid:
            await client.start_notify(uuid, notification_handler) 
            active_uuids.append(uuid)
        
        print(f"Listening on {len(active_uuids)} UUIDs for {device.listening_duration}s...")
        
        await asyncio.Future() 
        
        for uuid in active_uuids:
            await client.stop_notify(uuid)
        print("Listening stopped.")
        
    except Exception as e:
        print(f"The following exception occurred: {e}")


def notification_handler(sender: int, data: bytearray):
    global device
    if not device.pause_acquisition:
        try:
            decoded_string = data.decode('utf-8').strip()
            print(f"[{sender}] Data Decoded (UTF-8): {decoded_string}")
            parsed_row = parse_and_prepare_row(decoded_string)
            device.last_data = parsed_row 
            device.last_message = decoded_string 
            device.delta_time_notification = time.time() - device.last_message_time
            device.last_message_time = time.time()
            write_to_csv(parsed_row)
        except UnicodeDecodeError:
            print(f"[{sender}] Raw data (HEX): {data.hex()}")
        except Exception as e:
            print(f"[{sender}] Error: {e}")


def get_data_async():
    asyncio.run(scan_and_connect(device))

if __name__ == "__main__":
    try:
        setup_csv()
        device_thread = threading.Thread(target=get_data_async, daemon=True)
        device_thread.start()
        app.run(debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")