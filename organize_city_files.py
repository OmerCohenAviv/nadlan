import os
import shutil
import glob

base_dir = os.getcwd()
successful_dir = os.path.join(base_dir, 'successful_neighborhoods')

# Find all *_price_per_sqm_by_year.csv files
csv_files = glob.glob(os.path.join(base_dir, '*_price_per_sqm_by_year.csv'))
# Find all *_neighborhoods_residential folders
res_folders = [f for f in os.listdir(base_dir) if f.endswith('_neighborhoods_residential') and os.path.isdir(f)]

for csv_file in csv_files:
    city = os.path.basename(csv_file).replace('_price_per_sqm_by_year.csv', '')
    city_folder = os.path.join(base_dir, city)
    os.makedirs(city_folder, exist_ok=True)
    # Move CSV
    shutil.move(csv_file, os.path.join(city_folder, os.path.basename(csv_file)))
    # Move neighborhoods_residential folder if exists
    res_folder = f"{city}_neighborhoods_residential"
    if os.path.isdir(res_folder):
        shutil.move(res_folder, os.path.join(city_folder, res_folder))
    # Copy neighborhoods CSV from successful_neighborhoods
    # Try to find a file that contains the city name and ends with _neighborhoods.csv
    for f in os.listdir(successful_dir):
        if f.endswith('_neighborhoods.csv') and city in f:
            src = os.path.join(successful_dir, f)
            dst = os.path.join(city_folder, f)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            break
print("Organization complete.")