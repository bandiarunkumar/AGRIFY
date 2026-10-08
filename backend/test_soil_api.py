import requests

print("=== TEST: Soil API (Expected to be LIVE/Satellite without fallback watermark) ===")
try:
    r = requests.get(
        'http://127.0.0.1:5000/api/soil',
        params={'lat': '17.3850', 'lon': '78.4867'},
        timeout=30,
    )
    data = r.json()
    print(f"Status: {r.status_code}")
    print(f"ok: {data.get('ok')}")
    print(f"fallback: {data.get('fallback')}")
    print(f"source_name: {data.get('source_name')}")
    print(f"data_quality_note: {data.get('data_quality_note')}")
    print(f"Nitrogen: {data.get('nitrogen')}")
except Exception as e:
    print(f"Error: {e}")
