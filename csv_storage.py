import csv
import json
import time
import uuid
import logging

from utils import capture_browser_data


# CSV Headers
headers = ["timestamp", "website_id", "website_url", "web_requests"]

# Initialize CSV with headers
def initialize_csv(output_csv):
    logging.info(f"Initializing CSV file: {output_csv}")    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        

# Function to store data in the CSV file
def store_data_in_csv(timestamp, website_id, website_url, driver, output_csv_path="yt_measurements/default_output.csv"):
    data = capture_browser_data(driver)
    
    # Write to CSV
    with open(output_csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            website_id, 
            website_url, 
            json.dumps(data['web_requests'])
        ])