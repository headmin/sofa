import json
import csv
import argparse

# Parse command-line arguments for JSON and CSV file paths
parser = argparse.ArgumentParser(
    description="Update a CSV file with keys_of_interest data from JSON."
)
parser.add_argument("--json", required=True, help="Path to the input JSON file.")
parser.add_argument("--csv", required=True, help="Path to the output CSV file.")
args = parser.parse_args()

# Load the JSON data
with open(args.json, "r") as json_file:
    data = json.load(json_file)

# Define keys of interest, including nested keys
keys_of_interest = [
    "XProtectPayloads.com.apple.XProtectFramework.XProtect",
    "XProtectPayloads.com.apple.XprotectFramework.PluginService",
    "XProtectPayloads.ReleaseDate",
    "XProtectPlistConfigData.com.apple.XProtect",
    "XProtectPlistConfigData.ReleaseDate",
    "LatestMacOS.ProductVersion",
    "LatestMacOS.Build",
    "LatestMacOS.ReleaseDate",
]


# Flatten nested JSON data
def flatten(data, parent_key="", sep="."):
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


flattened_data = flatten(data)

# Filter the flattened JSON data to include only the keys of interest
data_filtered = {k: v for k, v in flattened_data.items() if k in keys_of_interest}

# Read existing CSV data
existing_data = []
try:
    with open(args.csv, mode="r", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        existing_data = list(reader)  # Convert to list of dictionaries
except FileNotFoundError:
    print("CSV file not found. A new one will be created.")

# Determine new or updated keys_of_interest data to append
data_to_append = []
for key, value in data_filtered.items():
    if not any(d["key"] == key and d["value"] == str(value) for d in existing_data):
        data_to_append.append({"key": key, "value": str(value)})

# Append new data
with open(args.csv, mode="a", newline="") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["key", "value"])
    if not existing_data:  # If file was not found or empty, write header
        writer.writeheader()
    writer.writerows(data_to_append)

print("CSV file has been updated with new data. Appended rows:", data_to_append)
