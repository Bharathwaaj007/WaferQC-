import re

f1 = open(r"E:\WaferQC\index.html", encoding="utf-8").read()
f2 = open(r"E:\WaferQC\dashboard.py", encoding="utf-8").read()

ui_apis = sorted(set(re.findall(r"/api/[a-zA-Z0-9_/]+", f1)))
backend_apis = sorted(set(re.findall(r'@app\.(?:get|post)\("([^"]+)"', f2)))

print("UI APIs:", ui_apis)
print("Backend APIs:", backend_apis)

missing_in_backend = [api for api in ui_apis if api not in backend_apis]
print("Missing in Backend:", missing_in_backend)
