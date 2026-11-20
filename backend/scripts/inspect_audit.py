import requests

r = requests.get("http://localhost:8000/api/audits/audit_20e402be3d")
data = r.json()
print(f"Total Pages: {data.get('pageCount')}")
for p in data.get("pages", []):
    print(f"\n==================== PAGE {p['pageNumber']} ====================")
    print(p['text'].strip())
