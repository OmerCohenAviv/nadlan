import os
import json
import glob
import pandas as pd
from collections import defaultdict

base_dir = os.getcwd()
folders = [f for f in os.listdir(base_dir) if f.endswith('_neighborhoods_residential') and os.path.isdir(f)]

def extract_year(deal_date):
    if not deal_date:
        return None
    # Try to extract year from various formats
    try:
        if isinstance(deal_date, int):
            return str(deal_date)[:4]
        if isinstance(deal_date, str):
            if len(deal_date) >= 4:
                return deal_date[:4]
    except Exception:
        return None
    return None

for folder in folders:
    city = folder.replace('_neighborhoods_residential', '')
    neighborhood_files = glob.glob(os.path.join(folder, '*.json'))
    data = defaultdict(lambda: defaultdict(list))  # data[neighborhood][year] = [price_per_sqm,...]
    neighborhoods = set()
    years = set()
    for json_file in neighborhood_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                node = json.load(f)
            neighborhood = node.get('neighborhood_name')
            transactions = node.get('transactions', [])
            for t in transactions:
                deal_amount = t.get('dealAmount')
                asset_area = t.get('assetArea')
                deal_date = t.get('dealDate')
                year = extract_year(deal_date)
                if not year or not deal_amount or not asset_area:
                    continue
                if year < '2006':
                    continue
                try:
                    price_per_sqm = float(deal_amount) / float(asset_area)
                    if price_per_sqm > 0 and price_per_sqm < 200000:  # sanity check
                        data[neighborhood][year].append(price_per_sqm)
                        neighborhoods.add(neighborhood)
                        years.add(year)
                except Exception:
                    continue
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    # Build DataFrame (rows=neighborhoods, columns=years)
    neighborhoods = sorted(list(neighborhoods))
    years = sorted([y for y in years if y >= '2006'])
    df = pd.DataFrame(index=neighborhoods, columns=years)
    for neighborhood in neighborhoods:
        for year in years:
            values = data[neighborhood][year]
            if values:
                df.at[neighborhood, year] = round(sum(values) / len(values), 2)
            else:
                df.at[neighborhood, year] = ''
    output_csv = f"{city}_price_per_sqm_by_year.csv"
    df.index.name = 'neighborhood'
    df.to_csv(output_csv, encoding='utf-8-sig')
    print(f"Saved {output_csv}")