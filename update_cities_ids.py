import csv

def update_cities_ids():
    """Update city IDs in cities.csv based on failed_cities_with_neighborhood.csv"""
    
    # Read the new IDs from failed_cities_with_neighborhood.csv
    new_ids = {}
    try:
        with open("failed_cities_with_neighborhood.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city_name = row.get('cityName', '').strip()
                city_id = row.get('cityId', '').strip()
                if city_name and city_id:
                    new_ids[city_name] = city_id
    except FileNotFoundError:
        print("❌ failed_cities_with_neighborhood.csv not found")
        return
    
    print(f"📋 Found {len(new_ids)} new city IDs to update")
    
    # Read current cities.csv
    cities = []
    try:
        with open("cities.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cities.append(row)
    except FileNotFoundError:
        print("❌ cities.csv not found")
        return
    
    print(f"📋 Found {len(cities)} cities in current cities.csv")
    
    # Update IDs
    updated_count = 0
    for city in cities:
        city_name = city.get('cityName', '').strip()
        old_id = city.get('cityId', '').strip()
        
        if city_name in new_ids:
            new_id = new_ids[city_name]
            if old_id != new_id:
                print(f"🔄 Updating {city_name}: {old_id} → {new_id}")
                city['cityId'] = new_id
                updated_count += 1
            else:
                print(f"✅ {city_name}: ID already correct ({old_id})")
        else:
            print(f"⏭️  {city_name}: No new ID found, keeping {old_id}")
    
    # Write updated cities.csv
    with open("cities_updated.csv", "w", encoding="utf-8", newline='') as f:
        fieldnames = ['cityId', 'cityName']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for city in cities:
            writer.writerow(city)
    
    print(f"\n🎉 Summary:")
    print(f"✅ Updated {updated_count} city IDs")
    print(f"💾 Saved updated file as cities_updated.csv")
    
    # Show which cities were updated
    if updated_count > 0:
        print(f"\n📋 Updated cities:")
        for city in cities:
            city_name = city.get('cityName', '').strip()
            if city_name in new_ids:
                print(f"  {city_name}: {city.get('cityId')}")

if __name__ == "__main__":
    update_cities_ids() 