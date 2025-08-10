import requests
import json
import base64
import gzip
import time
import hmac
import hashlib
import os
import csv
from typing import Dict, List, Set

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

def fetch_city_transactions(city_id: str, city_name: str, max_transactions: int = 100) -> List[Dict]:
    """Fetch transactions for a specific city"""
    
    print(f"🔍 Fetching transactions for {city_name} (ID: {city_id})...")
    
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
            # Create payload for this page
            data = {
                "base_id": city_id,
                "base_name": "settlmentID",
                "fetch_number": page_num,
                "type_order": "dealDate_down"
            }
            
            # Create JWT token
            jwt_token = create_jwt_token(data.copy())
            token_data = {"__": jwt_token}
            
            # Make request
            response = requests.post(url, json=token_data, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"    ❌ HTTP Error {response.status_code} for {city_name}")
                break
            
            # Handle response
            try:
                response_text = response.text
                if response_text:
                    try:
                        # Decode base64 and decompress
                        compressed_data = base64.b64decode(response_text)
                        decompressed_data = gzip.decompress(compressed_data).decode('utf-8')
                        result = json.loads(decompressed_data)
                        
                    except Exception as e:
                        # Try direct JSON parse
                        result = json.loads(response_text)
                
                # Extract transactions
                transactions = []
                if isinstance(result, list):
                    transactions = result
                elif isinstance(result, dict) and 'data' in result and 'items' in result['data']:
                    transactions = result['data']['items']
                elif isinstance(result, dict) and 'items' in result:
                    transactions = result['items']
                else:
                    print(f"    ❌ Unexpected response structure for {city_name}")
                    break
                
                if not transactions:
                    print(f"    ✅ No more transactions for {city_name}")
                    break
                
                # Add transactions to our collection
                for transaction in transactions:
                    if len(all_transactions) >= max_transactions:
                        break
                    all_transactions.append(transaction)
                
                print(f"    ✅ Added {len(transactions)} transactions for {city_name} (total: {len(all_transactions)})")
                
                # Check if we've reached our target
                if len(all_transactions) >= max_transactions:
                    break
                
                # Check if we got fewer than expected (might be last page)
                if len(transactions) < 50:
                    break
                
                # Delay between requests
                time.sleep(2)
                page_num += 1
                
            except Exception as e:
                print(f"    ❌ Error processing response for {city_name}: {e}")
                break
                
        except Exception as e:
            print(f"    ❌ Request error for {city_name}: {e}")
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

def check_if_neighborhoods_exist_in_transactions(transactions: List[Dict]) -> bool:
    """Check if any transactions have neighborhood data"""
    
    for transaction in transactions:
        if 'neighborhoodId' in transaction and 'neighborhoodName' in transaction:
            neighborhood_id = transaction['neighborhoodId']
            neighborhood_name = transaction['neighborhoodName']
            
            if neighborhood_id and neighborhood_name:
                return True
    
    return False

def get_cities_from_csv() -> Dict[str, str]:
    """Read cities from cities.csv file"""
    
    cities = {}
    
    try:
        with open("cities.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city_id = row.get('cityId', '').strip()
                city_name = row.get('cityName', '').strip()
                if city_id and city_name:
                    cities[city_id] = city_name
    except FileNotFoundError:
        print("❌ cities.csv file not found. Using default cities list.")
        # Fallback to known cities
        cities = {
            "3000": "ירושלים",
            "4000": "חיפה",
            "5000": "תל אביב-יפו",
            "6000": "באר שבע",
            "7000": "ראשון לציון",
            "8000": "פתח תקווה",
            "9000": "אשדוד",
            "7200": "נס ציונה"
        }
    
    return cities

def save_city_neighborhoods_to_csv(city_id: str, city_name: str, neighborhoods: Dict[str, str]):
    """Save neighborhoods for a specific city to CSV file in new folder"""
    
    os.makedirs('successful_neighborhoods', exist_ok=True)
    filename = f"successful_neighborhoods/{city_id}_{city_name}_neighborhoods.csv"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("cityId,cityName,neighborhoodId,neighborhoodName\n")
        for neighborhood_id, neighborhood_name in sorted(neighborhoods.items()):
            f.write(f"{city_id},{city_name},{neighborhood_id},{neighborhood_name}\n")
    
    print(f"💾 Saved {len(neighborhoods)} neighborhoods for {city_name} to {filename}")

def save_all_neighborhoods_to_csv(all_neighborhoods: Dict[str, Dict[str, str]], cities: Dict[str, str]):
    """Save all neighborhoods from all cities to a single CSV file in new folder"""
    
    os.makedirs('successful_neighborhoods', exist_ok=True)
    filename = "successful_neighborhoods/all_cities_neighborhoods.csv"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("cityId,cityName,neighborhoodId,neighborhoodName\n")
        for city_id, neighborhoods in all_neighborhoods.items():
            city_name = cities.get(city_id, f"עיר_{city_id}")
            for neighborhood_id, neighborhood_name in sorted(neighborhoods.items()):
                f.write(f"{city_id},{city_name},{neighborhood_id},{neighborhood_name}\n")
    
    print(f"💾 Saved all neighborhoods to {filename}")

def save_cities_without_neighborhoods(cities_without_neighborhoods: List[tuple]):
    """Save cities that have no neighborhoods at all"""
    
    os.makedirs('analysis_results', exist_ok=True)
    filename = "analysis_results/cities_without_neighborhoods.csv"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("cityId,cityName\n")
        for city_id, city_name in cities_without_neighborhoods:
            f.write(f"{city_id},{city_name}\n")
    
    print(f"💾 Saved {len(cities_without_neighborhoods)} cities without neighborhoods to {filename}")

def save_cities_with_extraction_issues(cities_with_extraction_issues: List[tuple]):
    """Save cities that have neighborhoods but couldn't be extracted"""
    
    os.makedirs('analysis_results', exist_ok=True)
    filename = "analysis_results/cities_with_extraction_issues.csv"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("cityId,cityName,reason\n")
        for city_id, city_name, reason in cities_with_extraction_issues:
            f.write(f"{city_id},{city_name},{reason}\n")
    
    print(f"💾 Saved {len(cities_with_extraction_issues)} cities with extraction issues to {filename}")

def save_failed_cities_to_csv(failed_cities: List[tuple]):
    """Save list of cities that failed to process completely"""
    
    os.makedirs('analysis_results', exist_ok=True)
    filename = "analysis_results/failed_cities.csv"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("cityId,cityName,reason\n")
        for city_id, city_name, reason in failed_cities:
            f.write(f"{city_id},{city_name},{reason}\n")
    
    print(f"💾 Saved {len(failed_cities)} failed cities to {filename}")

def main():
    """Main function to process all cities with enhanced categorization"""
    try:
        cities = get_cities_from_csv()
        all_neighborhoods = {}
        successful_cities = 0
        failed_cities = []
        cities_without_neighborhoods = []
        cities_with_extraction_issues = []
        
        print(f"🏙️ Starting to process {len(cities)} cities from cities.csv...")
        
        for city_id, city_name in cities.items():
            try:
                print(f"\n{'='*50}")
                print(f"Processing: {city_name} (ID: {city_id})")
                print(f"{'='*50}")
                
                # Fetch transactions for this city
                transactions = fetch_city_transactions(city_id, city_name, max_transactions=1000)
                
                if transactions:
                    # Check if neighborhoods exist in the data
                    neighborhoods_exist = check_if_neighborhoods_exist_in_transactions(transactions)
                    
                    if neighborhoods_exist:
                        # Try to extract neighborhoods
                        neighborhoods = extract_neighborhoods_from_transactions(transactions)
                        
                        if neighborhoods:
                            all_neighborhoods[city_id] = neighborhoods
                            successful_cities += 1
                            
                            print(f"✅ Found {len(neighborhoods)} neighborhoods in {city_name}:")
                            for neighborhood_id, neighborhood_name in sorted(neighborhoods.items()):
                                print(f"  {neighborhood_id}: {neighborhood_name}")
                            
                            # Save individual city file
                            save_city_neighborhoods_to_csv(city_id, city_name, neighborhoods)
                        else:
                            print(f"⚠️ Neighborhoods exist in data but couldn't be extracted for {city_name}")
                            cities_with_extraction_issues.append((city_id, city_name, "Neighborhoods exist but extraction failed"))
                    else:
                        print(f"❌ No neighborhoods found in transaction data for {city_name}")
                        cities_without_neighborhoods.append((city_id, city_name))
                else:
                    print(f"❌ No transactions found for {city_name}")
                    failed_cities.append((city_id, city_name, "No transactions found"))
                
                # Delay between cities
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Error processing {city_name}: {e}")
                failed_cities.append((city_id, city_name, f"Error: {e}"))
                continue
        
        # Save all results to appropriate files
        if all_neighborhoods:
            save_all_neighborhoods_to_csv(all_neighborhoods, cities)
        
        if cities_without_neighborhoods:
            save_cities_without_neighborhoods(cities_without_neighborhoods)
            
        if cities_with_extraction_issues:
            save_cities_with_extraction_issues(cities_with_extraction_issues)
            
        if failed_cities:
            save_failed_cities_to_csv(failed_cities)
            
        print(f"\n🎉 Summary:")
        print(f"✅ Successfully processed {successful_cities} out of {len(cities)} cities")
        print(f"❌ Failed to process {len(failed_cities)} cities")
        print(f"📍 Cities without neighborhoods: {len(cities_without_neighborhoods)}")
        print(f"⚠️ Cities with extraction issues: {len(cities_with_extraction_issues)}")
        print(f"🏘️ Total unique neighborhoods found: {sum(len(neighborhoods) for neighborhoods in all_neighborhoods.values())}")
        
        # Show top cities by neighborhood count
        if all_neighborhoods:
            city_neighborhood_counts = [(city_id, len(neighborhoods)) for city_id, neighborhoods in all_neighborhoods.items()]
            city_neighborhood_counts.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\n🏆 Top 10 cities by neighborhood count:")
            for i, (city_id, count) in enumerate(city_neighborhood_counts[:10]):
                city_name = cities.get(city_id, f"עיר_{city_id}")
                print(f"  {i+1}. {city_name}: {count} neighborhoods")
        
        # Show failed cities
        if failed_cities:
            print(f"\n❌ Failed cities:")
            for city_id, city_name, reason in failed_cities:
                print(f"  {city_id}: {city_name} - {reason}")
                
        # Show cities without neighborhoods
        if cities_without_neighborhoods:
            print(f"\n❌ Cities without neighborhoods:")
            for city_id, city_name in cities_without_neighborhoods:
                print(f"  {city_id}: {city_name}")
                
        # Show cities with extraction issues
        if cities_with_extraction_issues:
            print(f"\n⚠️ Cities with extraction issues:")
            for city_id, city_name, reason in cities_with_extraction_issues:
                print(f"  {city_id}: {city_name} - {reason}")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main() 