import os
import json

RESIDENTIAL_KEYWORDS = [
    "דירה", "פנטהאוז", "דירת גן", "דופלקס", "קוטג'", "קוטג", "בית", "יחידת דיור", "מגורים", "דירת קרקע", "דירת גג", "דירת פנטהאוז", "דירת דופלקס", "דירת גן", "פנטהאוז", "דופלקס"
]

INPUT_DIR = "ashdod_neighborhoods_transactions"
OUTPUT_DIR = "ashdod_neighborhoods_residential"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_residential(deal_nature):
    if not deal_nature:
        return False
    for keyword in RESIDENTIAL_KEYWORDS:
        if keyword in str(deal_nature):
            return True
    return False

def filter_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            data = []
    filtered = [deal for deal in data if is_residential(deal.get('dealNature', ''))]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    print(f"{os.path.basename(input_path)}: {len(filtered)} residential deals saved.")

def main():
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.json'):
            input_path = os.path.join(INPUT_DIR, filename)
            output_path = os.path.join(OUTPUT_DIR, filename)
            filter_file(input_path, output_path)

if __name__ == "__main__":
    main()