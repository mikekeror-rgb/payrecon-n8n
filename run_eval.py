"""Send each test payment to the n8n webhook and check the answer.

Deterministic cases (code paths) must pass exactly. Model cases must name a candidate or null,
and are reported separately, because a model answer can vary between runs.
Usage: python3 run_eval.py [base_url]   (default http://localhost:5678/webhook)
"""
import json, sys, urllib.request

base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5678/webhook"
cases = json.load(open("cases.json"))
# Start from no paid invoices, so every run is comparable.
urllib.request.urlopen(urllib.request.Request(f"{base}/mpesa-reset", data=b"{}", method="POST"), timeout=30)
code_pass = code_total = llm_pass = llm_total = 0
for case in cases:
    req = urllib.request.Request(f"{base}/mpesa-payment", data=json.dumps(case["payment"]).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        got = json.load(urllib.request.urlopen(req, timeout=60))
    except Exception as e:
        got = {"error": str(e)}
    exp = case["expect"]
    ok = got.get("status") == exp["status"]
    if "invoice" in exp: ok = ok and got.get("invoice") == exp["invoice"]
    if "reason_contains" in exp: ok = ok and exp["reason_contains"].lower() in str(got.get("reason", "")).lower()
    if "suggested_in" in exp:
        sug = (got.get("suggestion") or {}).get("invoice_id")
        ok = ok and sug in exp["suggested_in"]
    if exp.get("llm"):
        llm_total += 1; llm_pass += ok
    else:
        code_total += 1; code_pass += ok
    print(f"{'PASS' if ok else 'FAIL'}  {case['name']}: {json.dumps(got)[:160]}")
print(f"\nCode paths: {code_pass}/{code_total}   Model suggestions: {llm_pass}/{llm_total}")
sys.exit(0 if code_pass == code_total else 1)
