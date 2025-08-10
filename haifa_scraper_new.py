import requests
import json
import base64
import gzip
import time
import hmac
import hashlib
from typing import Dict, List

def create_jwt_token(payload: dict) -> str:
    """Create JWT token like the working try.py script"""
    header = {"typ": "JWT", "alg": "HS256"}
    current_time = int(time.time())
    
    # Add standard JWT fields
    payload_copy = payload.copy()
    payload_copy["iat"] = current_time
    payload_copy["exp"] = current_time + 120
    payload_copy["domain"] = "www.nadlan.gov.il"
    
    # Encode header and payload
    header_encoded = base64.urlsafe_b64encode(json.dumps(header, separators=(',', ':')).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload_copy, separators=(',', ':')).encode()).decode().rstrip('=')
    
    # Create signature
    message = f"{header_encoded}.{payload_encoded}"
    secret = "90c3e620192348f1bd46fcd9138c3c68"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    # Create JWT
    jwt_token = f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    
    # Reverse the token string
    return jwt_token[::-1]

def fetch_haifa_transactions(max_transactions: int = 1000) -> List[Dict]:
    """Fetch transactions for Haifa (city ID: 4000)"""
    
    print(f"🔍 Fetching transactions for חיפה (ID: 4000)...")
    print(f"📊 Target: {max_transactions} transactions")
    
    all_transactions = []
    page_num = 1
    
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
    
    url = 'https://x4006fhmy5.execute-api.il-central-1.amazonaws.com/api/deal'
    
    while len(all_transactions) < max_transactions:
        try:
            print(f"📄 Fetching page {page_num} (current transactions: {len(all_transactions)})...")
            
            # Create payload for this page
            data = {
                "base_id": "4000",  # Haifa city ID
                "base_name": "settlmentID",  # Note: keeping the typo as in working version
                "fetch_number": page_num,
                "type_order": "dealDate_down"
            }
            
            # Create JWT token
            jwt_token = create_jwt_token(data.copy())
            token_data = {"__": jwt_token}
            
            # Make request
            response = requests.post(url, json=token_data, headers=headers, timeout=30)
            
            print(f"    Status code: {response.status_code}")
            print(f"    Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"    Content-Length: {response.headers.get('Content-Length', 'unknown')}")
            
            if response.status_code != 200:
                print(f"    ❌ HTTP Error {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                break
            
            # Handle response
            try:
                # Try base64 gzipped response first
                response_text = response.text
                if response_text:
                    try:
                        # Decode base64 and decompress
                        compressed_data = base64.b64decode(response_text)
                        decompressed_data = gzip.decompress(compressed_data).decode('utf-8')
                        result = json.loads(decompressed_data)
                        print(f"    ✅ Successfully decompressed response!")
                        
                    except Exception as e:
                        # Try direct JSON parse
                        result = json.loads(response_text)
                        print(f"    ✅ Parsed as direct JSON")
                
                # Extract transactions
                transactions = []
                if isinstance(result, list):
                    transactions = result
                    print(f"    📊 Result is a list with {len(transactions)} items")
                elif isinstance(result, dict) and 'data' in result and 'items' in result['data']:
                    transactions = result['data']['items']
                    print(f"    📊 Found {len(transactions)} transactions in data.items")
                elif isinstance(result, dict) and 'items' in result:
                    transactions = result['items']
                    print(f"    📊 Found {len(transactions)} transactions in items")
                else:
                    print(f"    ❌ Unexpected response structure")
                    print(f"    Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    break
                
                if not transactions:
                    print(f"    ❌ No transactions found on page {page_num}")
                    break
                
                # Add transactions to our collection
                for transaction in transactions:
                    if len(all_transactions) >= max_transactions:
                        break
                    all_transactions.append(transaction)
                
                print(f"    ✅ Added {len(transactions)} transactions (total: {len(all_transactions)})")
                
                # Check if we've reached our target
                if len(all_transactions) >= max_transactions:
                    print(f"    ✅ Reached target of {max_transactions} transactions!")
                    break
                
                # Check if we got fewer than expected (might be last page)
                if len(transactions) < 50:
                    print(f"    📄 Got fewer than 50 transactions, might be last page")
                    break
                
                # Delay between requests
                delay = 3
                print(f"    ⏳ Waiting {delay} seconds...")
                time.sleep(delay)
                
                page_num += 1
                
            except Exception as e:
                print(f"    ❌ Error processing response: {e}")
                print(f"    Raw response preview: {response.text[:200]}")
                break
                
        except Exception as e:
            print(f"    ❌ Request error: {e}")
            time.sleep(5)
            continue
    
    return all_transactions

def extract_neighborhoods_from_transactions(transactions: List[Dict]) -> Dict[str, str]:
    """Extract unique neighborhoods from transactions"""
    
    neighborhoods = {}
    
    for transaction in transactions:
        if 'neighborhoodId' in transaction and 'neighborhoodName' in transaction:
            neighborhood_id = str(transaction['neighborhoodId'])
            neighborhood_name = transaction['neighborhoodName']
            
            if neighborhood_id and neighborhood_name:
                neighborhoods[neighborhood_id] = neighborhood_name
    
    return neighborhoods

def save_transactions_to_json(transactions: List[Dict], filename: str):
    """Save transactions to JSON file"""
    
    output_data = {
        "cityName": "חיפה",
        "settlementId": "4000",
        "totalTransactions": len(transactions),
        "transactions": transactions
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saved {len(transactions)} transactions to {filename}")

def save_neighborhoods_to_csv(neighborhoods: Dict[str, str], filename: str):
    """Save neighborhoods to CSV file"""
    
    import os
    os.makedirs('csv_output', exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("neighborhoodId,neighborhoodName\n")
        for neighborhood_id, neighborhood_name in sorted(neighborhoods.items()):
            f.write(f"{neighborhood_id},{neighborhood_name}\n")
    
    print(f"💾 Saved {len(neighborhoods)} neighborhoods to {filename}")

def main():
    """Main function"""
    try:
        # Fetch transactions
        transactions = fetch_haifa_transactions(max_transactions=1000)
        
        if not transactions:
            print("❌ No transactions found for חיפה")
            return
        
        print(f"\n🎉 Successfully fetched {len(transactions)} transactions!")
        
        # Extract neighborhoods
        neighborhoods = extract_neighborhoods_from_transactions(transactions)
        print(f"📍 Found {len(neighborhoods)} unique neighborhoods:")
        
        # Sort and display neighborhoods
        sorted_neighborhoods = sorted(neighborhoods.items(), key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'))
        for neighborhood_id, neighborhood_name in sorted_neighborhoods:
            print(f"  {neighborhood_id}: {neighborhood_name}")
        
        # Save data
        save_transactions_to_json(transactions, "haifa_transactions.json")
        save_neighborhoods_to_csv(neighborhoods, "csv_output/haifa_neighborhoods.csv")
        
        # Show some sample transactions
        print(f"\n📋 Sample transactions:")
        for i, transaction in enumerate(transactions[:3]):
            print(f"\nTransaction {i+1}:")
            print(f"  Deal Amount: {transaction.get('dealAmount', 'N/A')}")
            print(f"  Deal Year: {transaction.get('dealYear', 'N/A')}")
            print(f"  Neighborhood: {transaction.get('neighborhoodName', 'N/A')}")
            print(f"  Address: {transaction.get('assetAddress', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main() 