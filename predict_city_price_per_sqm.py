import os
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

base_dir = os.getcwd()
city_folders = [f for f in os.listdir(base_dir) if os.path.isdir(f) and not f.startswith('.')]

for city in city_folders:
    csv_path = os.path.join(base_dir, city, f"{city}_price_per_sqm_by_year.csv")
    if not os.path.exists(csv_path):
        continue
    df = pd.read_csv(csv_path, index_col=0)
    # Ensure columns are years and sorted
    years = [c for c in df.columns if c.isdigit() and int(c) <= 2030]
    years = sorted(years)
    # Prepare for predictions
    for pred_year in range(2026, 2031):
        df[str(pred_year)] = ''
    for idx, row in df.iterrows():
        # Gather historical data
        x = []
        y = []
        for year in years:
            val = row[year]
            if pd.notnull(val) and str(val).strip() != '':
                try:
                    x.append(int(year))
                    y.append(float(val))
                except Exception:
                    continue
        if len(x) >= 2:
            X = np.array(x).reshape(-1, 1)
            y = np.array(y)
            model = LinearRegression()
            model.fit(X, y)
            for pred_year in range(2026, 2031):
                pred = model.predict(np.array([[pred_year]]))[0]
                if pred > 0 and pred < 200000:
                    df.at[idx, str(pred_year)] = round(pred, 2)
                else:
                    df.at[idx, str(pred_year)] = ''
        else:
            for pred_year in range(2026, 2031):
                df.at[idx, str(pred_year)] = ''
    # Save back to CSV
    df.to_csv(csv_path, encoding='utf-8-sig')
    print(f"Updated {csv_path} with predictions for 2026-2030.")