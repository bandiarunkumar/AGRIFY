import requests
import json

# Test the updated market API
print("=== TEST: Tomato in Telangana ===")
try:
    r = requests.post(
        'http://127.0.0.1:5000/api/market-prices',
        json={'crop': 'tomato', 'state': 'Telangana'},
        timeout=30,
    )
    data = r.json()
    print(f"Status: {r.status_code}")
    print(f"Markets returned: {len(data.get('markets', []))}")
    print(f"Total reporting: {data.get('total_markets_reporting')}")
    print(f"Data quality: {data.get('data_quality')}")
    print(f"Is fallback: {data.get('is_fallback')}")
    print(f"Avg price/kg: {data.get('avg_price_per_kg')}")
    print(f"Best market: {data.get('best_market')}")
    print(f"Source: {data.get('source_name')}")

    # Show first 5 markets
    for i, m in enumerate(data.get('markets', [])[:8]):
        print(f"  {i+1}. {m['name']} ({m['district']}) - ₹{m['price_per_kg']}/kg | ₹{m['price_per_quintal']}/q")
except Exception as e:
    print(f"Error: {e}")

print("\n=== TEST: Tomato in Hyderabad district ===")
try:
    r2 = requests.post(
        'http://127.0.0.1:5000/api/market-prices',
        json={'crop': 'tomato', 'state': 'Telangana', 'district': 'Hyderabad'},
        timeout=30,
    )
    data2 = r2.json()
    print(f"Markets returned: {len(data2.get('markets', []))}")
    for m in data2.get('markets', []):
        print(f"  {m['name']} ({m['district']}) - ₹{m['price_per_kg']}/kg")
except Exception as e:
    print(f"Error: {e}")

print("\n=== TEST: Cotton in Telangana ===")
try:
    r3 = requests.post(
        'http://127.0.0.1:5000/api/market-prices',
        json={'crop': 'cotton', 'state': 'Telangana'},
        timeout=30,
    )
    data3 = r3.json()
    print(f"Markets returned: {len(data3.get('markets', []))}")
    print(f"Avg price/kg: {data3.get('avg_price_per_kg')}")
    for m in data3.get('markets', [])[:5]:
        print(f"  {m['name']} ({m['district']}) - ₹{m['price_per_kg']}/kg")
except Exception as e:
    print(f"Error: {e}")
