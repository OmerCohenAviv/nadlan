import os
import json
import glob

# Find all *_neighborhoods_residential folders
base_dir = os.getcwd()
folders = [f for f in os.listdir(base_dir) if f.endswith('_neighborhoods_residential') and os.path.isdir(f)]

deleted_files = []
for folder in folders:
    json_files = glob.glob(os.path.join(folder, '*.json'))
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get('transaction_count', 0) < 30:
                os.remove(json_file)
                deleted_files.append(json_file)
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

print(f"Deleted {len(deleted_files)} files with less than 30 deals.")