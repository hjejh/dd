import requests

BASE_URL = "https://openapivts.koreainvestment.com:29443"
APPKEY="PSwZRK73xeWmV03C3C8qjdCTqoPNpClRLKhf"
APPSECRET="EUaMe/qTjQCrZcpcvKKEjYrf1XaDb+HCRADiwMLWyBkh7oOY4sk6pnDR5GSPDrvohB+pJwvinztPtdT+i9E3C0u2VfgAbZWWwV2tQdjzemqnI1/DsvELnsfpKR0q3o2QSMnis0BwMGFo6AHCjj+kC+pge6UoLCF4TiggZmUre7EMBMANHzA="

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImQxMGNhMDgxLTcxYzUtNDUwNS1hYmIyLThlZTU3Y2Y4NGU0ZSIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTc1NDM4ODI0MywiaWF0IjoxNzU0MzAxODQzLCJqdGkiOiJQU3daUks3M3hlV21WMDNDM0M4cWpkQ1Rxb1BOcENsUkxLaGYifQ.bp8ErIBfAjJrZv1eCzkYCm37Z1kyHyoWUfzSFDvX5BAq73O80yCF1KIxjyE79nmzgfVZ5di_fJa6qemg1oimdw"

def fetch_current_price(code):
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "FHKST01010100"
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code
    }
    res = requests.get(url, headers=headers, params=params)
    try:
        data = res.json()
        return int(data["output"]["stck_prpr"])
    except Exception as e:
        print(e)
        return None

print(fetch_current_price("005930"))

