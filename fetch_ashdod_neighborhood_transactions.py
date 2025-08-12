import os
import csv
import json
import requests
import base64
import gzip
import time
import hmac
import hashlib

def create_jwt_token(payload: dict) -> str:
    header = {"typ": "JWT", "alg": "HS256"}
    current_time = int(time.time())
    payload_copy = payload.copy()
    payload_copy["iat"] = current_time
    payload_copy["exp"] = current_time + 120
    payload_copy["domain"] = "www.nadlan.gov.il"
    header_encoded = base64.urlsafe_b64encode(json.dumps(header, separators=(',', ':')).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload_copy, separators=(',', ':')).encode()).decode().rstrip('=')
    message = f"{header_encoded}.{payload_encoded}"
    secret = "90c3e620192348f1bd46fcd9138c3c68"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    jwt_token = f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    return jwt_token[::-1]

def fetch_neighborhood_transactions(neighborhood_id: str, neighborhood_name: str, max_transactions: int = 1000) -> list:
    url = 'https://x4006fhmy5.execute-api.il-central-1.amazonaws.com/api/deal'
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nadlan.gov.il/",
        "Origin": "https://www.nadlan.gov.il",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    all_transactions = []
    page_num = 1
    while len(all_transactions) < max_transactions:
        data = {
            "base_id": neighborhood_id,
            "base_name": "neighborhoodId",
            "fetch_number": page_num,
            "type_order": "dealDate_down"
        }
        jwt_token = create_jwt_token(data.copy())
        token_data = {"__": jwt_token}
        try:
            response = requests.post(url, json=token_data, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"    ❌ HTTP Error {response.status_code} for {neighborhood_name}")
                break
            response_text = response.text
            if response_text:
                try:
                    compressed_data = base64.b64decode(response_text)
                    decompressed_data = gzip.decompress(compressed_data).decode('utf-8')
                    result = json.loads(decompressed_data)
                except Exception:
                    result = json.loads(response_text)
                transactions = []
                if isinstance(result, list):
                    transactions = result
                elif isinstance(result, dict) and 'data' in result and 'items' in result['data']:
                    transactions = result['data']['items']
                elif isinstance(result, dict) and 'items' in result:
                    transactions = result['items']
                else:
                    break
                if not transactions:
                    break
                for transaction in transactions:
                    if len(all_transactions) >= max_transactions:
                        break
                    all_transactions.append(transaction)
                if len(transactions) < 50:
                    break
                page_num += 1
                time.sleep(1)
            else:
                break
        except Exception as e:
            print(f"    ❌ Error fetching transactions for {neighborhood_name}: {e}")
            break
    return all_transactions

def main():
    input_file = "successful_neighborhoods/70_אשדוד_neighborhoods.csv"
    output_dir = "ashdod_neighborhoods_transactions"
    os.makedirs(output_dir, exist_ok=True)
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            neighborhood_id = row['neighborhoodId']
            neighborhood_name = row['neighborhoodName'].replace('/', '_').replace(' ', '_')
            print(f"🔍 Fetching transactions for {neighborhood_name} ({neighborhood_id})...")
            transactions = fetch_neighborhood_transactions(neighborhood_id, neighborhood_name, max_transactions=1000)
            output_path = os.path.join(output_dir, f"{neighborhood_id}_{neighborhood_name}.json")
            with open(output_path, 'w', encoding='utf-8') as out_f:
                json.dump(transactions, out_f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {len(transactions)} transactions to {output_path}")
            time.sleep(2)

if __name__ == "__main__":
    main()